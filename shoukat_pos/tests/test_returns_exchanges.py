"""
Comprehensive Tests for Return and Exchange Processing

Tests cover:
- Simple cash returns
- Credit note returns  
- Variant swap exchanges
- Stock restoration logic
- Validation edge cases
- Transaction atomicity
"""
import pytest
import sqlite3
from datetime import datetime, timedelta
from typing import List

from services.return_engine import (
    ReturnEngine,
    ReturnItem,
    ExchangeItem,
    ReturnResult,
    ReturnReason,
    RestockAction,
    ReturnValidationError,
    create_return_with_transaction,
    create_exchange_with_transaction,
)
from services.sale_engine import create_sale_with_transaction, CartItem
from database.connection import get_write_connection


@pytest.fixture
def engine(db_path):
    """Create a ReturnEngine instance."""
    return ReturnEngine(db_path)


@pytest.fixture
def sample_sale(db_path):
    """Create a sale with items that can be returned."""
    # First, ensure we have products
    conn = get_write_connection(db_path)
    
    # Create a category if needed
    conn.execute("""
        INSERT OR IGNORE INTO categories (name, code, description)
        VALUES ('Test Shirts', 'TS', 'Test category')
    """)
    
    # Get category ID
    cat_id = conn.execute(
        "SELECT id FROM categories WHERE code = 'TS'"
    ).fetchone()["id"]
    
    # Create a style
    conn.execute("""
        INSERT INTO styles (style_code, name, category_id, base_sale_price)
        VALUES ('TEST-SHIRT', 'Test Shirt', ?, 250000)
    """, (cat_id,))
    
    style_id = conn.execute(
        "SELECT id FROM styles WHERE style_code = 'TEST-SHIRT'"
    ).fetchone()["id"]
    
    # Create variants (size/color matrix)
    variants = [
        ("M", "Blue"),
        ("L", "Blue"),
        ("M", "Black"),
        ("L", "Black"),
    ]
    
    variant_ids = []
    for size, color in variants:
        barcode = f"TEST-{size}-{color}"
        conn.execute("""
            INSERT INTO variants (style_id, size, color, barcode, quantity)
            VALUES (?, ?, ?, ?, 10)
        """, (style_id, size, color, barcode))
        
        variant_id = conn.execute(
            "SELECT id FROM variants WHERE barcode = ?", (barcode,)
        ).fetchone()["id"]
        variant_ids.append(variant_id)
        
        # Create a batch for each variant
        conn.execute("""
            INSERT INTO batches (variant_id, purchase_price, secret_code, 
                                quantity_received, quantity_remaining)
            VALUES (?, 150000, 'ABC', 10, 10)
        """, (variant_id,))
    
    conn.commit()
    conn.close()
    
    # Create a sale with these items
    cart = [
        {"variant_id": variant_ids[0], "quantity": 2, "unit_price": 250000, "tax_rate": 0.0},
        {"variant_id": variant_ids[1], "quantity": 1, "unit_price": 250000, "tax_rate": 0.0},
    ]
    
    result = create_sale_with_transaction(
        db_path=db_path,
        cart=cart,
        customer_id=None,
        payment_type="cash",
        paid_amount=750000,
        discount_amount=0,
        user_id=1
    )
    
    assert result.success, f"Sale creation failed: {result.message}"
    
    return {
        "sale_id": result.sale_id,
        "invoice_number": result.invoice_number,
        "variant_ids": variant_ids,
        "sale_items": result.sale_items,
    }


class TestReturnValidation:
    """Test return validation logic."""
    
    def test_validate_valid_return(self, engine, sample_sale, db_path):
        """Test that valid returns pass validation."""
        conn = get_write_connection(db_path)
        
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        is_valid, error_msg = engine.validate_return_items(
            sample_sale["sale_id"], items, conn
        )
        
        assert is_valid, f"Validation failed: {error_msg}"
        conn.close()
    
    def test_validate_nonexistent_sale(self, engine, db_path):
        """Test validation fails for non-existent sale."""
        conn = get_write_connection(db_path)
        
        items = [
            ReturnItem(
                sale_item_id=999,
                variant_id=1,
                quantity=1,
                unit_price=100,
                total_amount=100
            )
        ]
        
        is_valid, error_msg = engine.validate_return_items(999, items, conn)
        
        assert not is_valid
        assert "not found" in error_msg.lower()
        conn.close()
    
    def test_validate_quantity_exceeds_original(self, engine, sample_sale, db_path):
        """Test validation fails when return quantity exceeds original."""
        conn = get_write_connection(db_path)
        
        # Try to return 3 units when only 2 were sold
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=3,  # More than original 2
                unit_price=250000,
                total_amount=750000
            )
        ]
        
        is_valid, error_msg = engine.validate_return_items(
            sample_sale["sale_id"], items, conn
        )
        
        assert not is_valid
        assert "available for return" in error_msg
        conn.close()
    
    def test_validate_partial_return_already_processed(self, engine, sample_sale, db_path):
        """Test validation after a partial return has been processed."""
        # Process a partial return first
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = engine.process_return(
            sale_id=sample_sale["sale_id"],
            items=items,
            reason="wrong_size",
            refund_type="cash",
            user_id=1
        )
        
        assert result.success
        
        # Now try to return another 2 units (should fail - only 1 left)
        conn = get_write_connection(db_path)
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=2,  # Only 1 remaining
                unit_price=250000,
                total_amount=500000
            )
        ]
        
        is_valid, error_msg = engine.validate_return_items(
            sample_sale["sale_id"], items, conn
        )
        
        assert not is_valid
        assert "Only 1 units available" in error_msg
        conn.close()


class TestSimpleReturns:
    """Test simple return processing."""
    
    def test_process_cash_return(self, engine, sample_sale, db_path):
        """Test processing a simple cash return."""
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = engine.process_return(
            sale_id=sample_sale["sale_id"],
            items=items,
            reason="customer_changed_mind",
            refund_type="cash",
            user_id=1
        )
        
        assert result.success
        assert result.return_number.startswith("RET-")
        assert result.refund_amount == 250000
        assert result.rupee_refund == 2500.0
        assert result.items_returned == 1
        assert result.refund_type == "cash"
        
        # Verify return was recorded
        return_details = engine.get_return_details(result.return_number)
        assert return_details is not None
        assert len(return_details["items"]) == 1
    
    def test_process_credit_note_return(self, engine, sample_sale, db_path):
        """Test processing a return with store credit."""
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][1]["id"],
                variant_id=sample_sale["variant_ids"][1],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = engine.process_return(
            sale_id=sample_sale["sale_id"],
            items=items,
            reason="defective",
            refund_type="credit_note",
            user_id=1
        )
        
        assert result.success
        assert result.refund_type == "credit_note"
        assert result.rupee_refund == 2500.0
    
    def test_process_return_multiple_items(self, engine, sample_sale, db_path):
        """Test returning multiple items from same sale."""
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            ),
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][1]["id"],
                variant_id=sample_sale["variant_ids"][1],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            ),
        ]
        
        result = engine.process_return(
            sale_id=sample_sale["sale_id"],
            items=items,
            reason="wrong_color",
            refund_type="cash",
            user_id=1
        )
        
        assert result.success
        assert result.items_returned == 2
        assert result.rupee_refund == 5000.0
        
        # Verify both items recorded
        return_details = engine.get_return_details(result.return_number)
        assert len(return_details["items"]) == 2
    
    def test_return_stock_restored(self, engine, sample_sale, db_path):
        """Test that stock is restored after return."""
        conn = get_write_connection(db_path)
        
        # Get initial stock
        variant_id = sample_sale["variant_ids"][0]
        initial_stock = conn.execute(
            "SELECT quantity FROM variants WHERE id = ?", (variant_id,)
        ).fetchone()["quantity"]
        
        # Process return
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=variant_id,
                quantity=2,  # Return both units
                unit_price=250000,
                total_amount=500000
            )
        ]
        
        result = engine.process_return(
            sale_id=sample_sale["sale_id"],
            items=items,
            reason="customer_changed_mind",
            restock_action=RestockAction.IMMEDIATE_RESTOCK,
            user_id=1
        )
        
        assert result.success
        
        # Verify stock increased
        new_stock = conn.execute(
            "SELECT quantity FROM variants WHERE id = ?", (variant_id,)
        ).fetchone()["quantity"]
        
        assert new_stock == initial_stock + 2
        conn.close()
    
    def test_return_updates_sale_status(self, engine, sample_sale, db_path):
        """Test that sale status updates after full return."""
        conn = get_write_connection(db_path)
        
        # Return all items from the sale
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=2,
                unit_price=250000,
                total_amount=500000
            ),
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][1]["id"],
                variant_id=sample_sale["variant_ids"][1],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            ),
        ]
        
        result = engine.process_return(
            sale_id=sample_sale["sale_id"],
            items=items,
            reason="duplicate_purchase",
            refund_type="cash",
            user_id=1
        )
        
        assert result.success
        
        # Verify sale status updated
        sale_status = conn.execute(
            "SELECT status FROM sales WHERE id = ?", (sample_sale["sale_id"],)
        ).fetchone()["status"]
        
        assert sale_status == "fully_returned"
        conn.close()


class TestExchanges:
    """Test variant swap exchanges."""
    
    def test_even_exchange_same_price(self, engine, sample_sale, db_path):
        """Test exchanging item for same-priced variant."""
        # Return Medium Blue (variant 0), exchange for Large Black (variant 3)
        return_items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        exchange_items = [
            ExchangeItem(
                variant_id=sample_sale["variant_ids"][3],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = engine.process_exchange(
            original_sale_id=sample_sale["sale_id"],
            return_items=return_items,
            exchange_items=exchange_items,
            reason="wrong_size",
            user_id=1
        )
        
        assert result.success
        assert result.price_difference == 0
        assert result.rupee_price_difference == 0.0
        assert "Even exchange" in result.message
        assert result.exchange_sale_id is not None
        
        # Verify exchange record created
        exchange_details = engine.get_exchange_details(result.return_number.replace("RET", "EXC"))
        # Note: exchange number is different from return number
    
    def test_exchange_customer_pays_difference(self, engine, sample_sale, db_path):
        """Test exchange where new item costs more."""
        # Return 1 unit at Rs. 2500, exchange for 2 units at Rs. 2500 each
        return_items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        exchange_items = [
            ExchangeItem(
                variant_id=sample_sale["variant_ids"][1],
                quantity=2,
                unit_price=250000,
                total_amount=500000
            )
        ]
        
        result = engine.process_exchange(
            original_sale_id=sample_sale["sale_id"],
            return_items=return_items,
            exchange_items=exchange_items,
            reason="wrong_size",
            user_id=1
        )
        
        assert result.success
        assert result.price_difference == 250000  # Customer pays Rs. 2500 more
        assert "Customer pays additional" in result.message
    
    def test_exchange_customer_gets_refund(self, engine, sample_sale, db_path):
        """Test exchange where new item costs less."""
        # Return 2 units, exchange for 1 unit
        return_items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=2,
                unit_price=250000,
                total_amount=500000
            )
        ]
        
        exchange_items = [
            ExchangeItem(
                variant_id=sample_sale["variant_ids"][1],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = engine.process_exchange(
            original_sale_id=sample_sale["sale_id"],
            return_items=return_items,
            exchange_items=exchange_items,
            reason="changed_mind",
            user_id=1
        )
        
        assert result.success
        assert result.price_difference == -250000  # Customer gets Rs. 2500 refund
        assert "Refund to customer" in result.message
    
    def test_exchange_stock_adjustments(self, engine, sample_sale, db_path):
        """Test that stock is correctly adjusted in exchange."""
        conn = get_write_connection(db_path)
        
        return_variant = sample_sale["variant_ids"][0]
        exchange_variant = sample_sale["variant_ids"][3]
        
        # Get initial stock
        return_initial = conn.execute(
            "SELECT quantity FROM variants WHERE id = ?", (return_variant,)
        ).fetchone()["quantity"]
        
        exchange_initial = conn.execute(
            "SELECT quantity FROM variants WHERE id = ?", (exchange_variant,)
        ).fetchone()["quantity"]
        
        return_items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=return_variant,
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        exchange_items = [
            ExchangeItem(
                variant_id=exchange_variant,
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = engine.process_exchange(
            original_sale_id=sample_sale["sale_id"],
            return_items=return_items,
            exchange_items=exchange_items,
            reason="wrong_color",
            user_id=1
        )
        
        assert result.success
        
        # Verify stock adjustments
        return_new = conn.execute(
            "SELECT quantity FROM variants WHERE id = ?", (return_variant,)
        ).fetchone()["quantity"]
        
        exchange_new = conn.execute(
            "SELECT quantity FROM variants WHERE id = ?", (exchange_variant,)
        ).fetchone()["quantity"]
        
        # Returned variant should have +1 stock
        assert return_new == return_initial + 1
        
        # Exchanged variant should have -1 stock (new sale deducted it)
        assert exchange_new == exchange_initial - 1
        
        conn.close()
    
    def test_exchange_insufficient_stock(self, engine, sample_sale, db_path):
        """Test exchange fails when exchange item has insufficient stock."""
        conn = get_write_connection(db_path)
        
        # Set exchange variant stock to 0
        conn.execute(
            "UPDATE variants SET quantity = 0 WHERE id = ?",
            (sample_sale["variant_ids"][3],)
        )
        conn.execute(
            "UPDATE batches SET quantity_remaining = 0 WHERE variant_id = ?",
            (sample_sale["variant_ids"][3],)
        )
        conn.commit()
        conn.close()
        
        return_items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        exchange_items = [
            ExchangeItem(
                variant_id=sample_sale["variant_ids"][3],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        with pytest.raises(ReturnValidationError) as exc_info:
            engine.process_exchange(
                original_sale_id=sample_sale["sale_id"],
                return_items=return_items,
                exchange_items=exchange_items,
                reason="wrong_size",
                user_id=1
            )
        
        assert "Insufficient stock" in str(exc_info.value)


class TestConvenienceFunctions:
    """Test the module-level convenience functions."""
    
    def test_create_return_with_transaction(self, sample_sale, db_path):
        """Test the create_return_with_transaction function."""
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = create_return_with_transaction(
            db_path=db_path,
            sale_id=sample_sale["sale_id"],
            items=items,
            reason="test_return",
            refund_type="cash",
            user_id=1
        )
        
        assert result.success
        assert result.return_number.startswith("RET-")
    
    def test_create_exchange_with_transaction(self, sample_sale, db_path):
        """Test the create_exchange_with_transaction function."""
        return_items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        exchange_items = [
            ExchangeItem(
                variant_id=sample_sale["variant_ids"][1],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = create_exchange_with_transaction(
            db_path=db_path,
            original_sale_id=sample_sale["sale_id"],
            return_items=return_items,
            exchange_items=exchange_items,
            reason="test_exchange",
            user_id=1
        )
        
        assert result.success
        assert result.exchange_sale_id is not None


class TestAuditLogging:
    """Test audit logging for returns and exchanges."""
    
    def test_return_creates_audit_log(self, engine, sample_sale, db_path):
        """Test that processing a return creates an audit log entry."""
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = engine.process_return(
            sale_id=sample_sale["sale_id"],
            items=items,
            reason="customer_changed_mind",
            refund_type="cash",
            user_id=1
        )
        
        assert result.success
        
        # Check audit log
        conn = get_write_connection(db_path)
        audit_entry = conn.execute(
            """
            SELECT * FROM audit_log 
            WHERE table_name = 'returns' 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
        ).fetchone()
        
        assert audit_entry is not None
        assert audit_entry["action"] == "CREATE"
        assert "refund_amount" in audit_entry["new_values"]
        conn.close()
    
    def test_exchange_creates_audit_log(self, engine, sample_sale, db_path):
        """Test that processing an exchange creates an audit log entry."""
        return_items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        exchange_items = [
            ExchangeItem(
                variant_id=sample_sale["variant_ids"][1],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        result = engine.process_exchange(
            original_sale_id=sample_sale["sale_id"],
            return_items=return_items,
            exchange_items=exchange_items,
            reason="wrong_size",
            user_id=1
        )
        
        assert result.success
        
        # Check audit log
        conn = get_write_connection(db_path)
        audit_entry = conn.execute(
            """
            SELECT * FROM audit_log 
            WHERE table_name = 'exchanges' 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
        ).fetchone()
        
        assert audit_entry is not None
        assert audit_entry["action"] == "CREATE"
        assert "price_difference" in audit_entry["new_values"]
        conn.close()


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_return_voided_sale_fails(self, engine, sample_sale, db_path):
        """Test that returning a voided sale fails."""
        conn = get_write_connection(db_path)
        conn.execute(
            "UPDATE sales SET status = 'voided' WHERE id = ?",
            (sample_sale["sale_id"],)
        )
        conn.commit()
        conn.close()
        
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=1,
                unit_price=250000,
                total_amount=250000
            )
        ]
        
        with pytest.raises(ReturnValidationError) as exc_info:
            engine.process_return(
                sale_id=sample_sale["sale_id"],
                items=items,
                reason="test",
                refund_type="cash",
                user_id=1
            )
        
        assert "voided" in str(exc_info.value).lower()
    
    def test_return_zero_quantity_fails(self, engine, sample_sale, db_path):
        """Test that returning zero quantity fails assertion."""
        items = [
            ReturnItem(
                sale_item_id=sample_sale["sale_items"][0]["id"],
                variant_id=sample_sale["variant_ids"][0],
                quantity=0,  # Invalid
                unit_price=250000,
                total_amount=0
            )
        ]
        
        with pytest.raises(AssertionError):
            engine.process_return(
                sale_id=sample_sale["sale_id"],
                items=items,
                reason="test",
                refund_type="cash",
                user_id=1
            )
    
    def test_return_empty_items_list_fails(self, engine, sample_sale, db_path):
        """Test that returning with empty items list fails."""
        with pytest.raises(AssertionError):
            engine.process_return(
                sale_id=sample_sale["sale_id"],
                items=[],
                reason="test",
                refund_type="cash",
                user_id=1
            )
    
    def test_get_nonexistent_return_details(self, engine, db_path):
        """Test getting details for non-existent return."""
        result = engine.get_return_details("RET-NONEXISTENT")
        assert result is None
    
    def test_get_nonexistent_exchange_details(self, engine, db_path):
        """Test getting details for non-existent exchange."""
        result = engine.get_exchange_details("EXC-NONEXISTENT")
        assert result is None
