"""
Comprehensive tests for the Sale Processing Engine.

This module tests all aspects of the sale engine including:
- Cart validation
- Total calculations
- Stock deduction
- Sale creation
- Customer credit handling
- Loyalty points accrual
- Gift card redemption
- Error handling and edge cases
"""

import pytest
import sqlite3
from typing import List

from services.sale_engine import (
    SaleEngine, 
    CartItem, 
    PaymentInfo, 
    SaleResult,
    create_sale_with_transaction
)
from database.models import Sale, SaleItem
from utils.audit_logger import AuditLogger


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sale_engine() -> SaleEngine:
    """Create a sale engine instance."""
    return SaleEngine()


@pytest.fixture
def sample_cart(sample_variant: dict, sample_batch: dict) -> List[CartItem]:
    """Create a sample cart with one item."""
    return [
        CartItem(
            variant_id=sample_variant["id"],
            batch_id=sample_batch["id"],
            quantity=2,
            unit_price=220000,  # Rs. 2,200 in cents
            tax_rate=0.0,
        )
    ]


# =============================================================================
# CART VALIDATION TESTS
# =============================================================================

class TestCartValidation:
    """Test cart validation logic."""
    
    def test_empty_cart_raises_error(
        self, 
        db_connection: sqlite3.Connection, 
        sale_engine: SaleEngine
    ):
        """Empty cart should raise assertion error."""
        with pytest.raises(AssertionError, match="Cart cannot be empty"):
            sale_engine._validate_cart(db_connection, [])
    
    def test_invalid_variant_id(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine
    ):
        """Non-existent variant should return validation error."""
        cart = [
            CartItem(
                variant_id=99999,
                batch_id=1,
                quantity=1,
                unit_price=100000,
            )
        ]
        is_valid, error_msg = sale_engine._validate_cart(db_connection, cart)
        
        assert not is_valid
        assert "not found" in error_msg
    
    def test_insufficient_stock(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_variant: dict
    ):
        """Requesting more than available stock should fail."""
        cart = [
            CartItem(
                variant_id=sample_variant["id"],
                batch_id=99999,
                quantity=1000,  # More than available
                unit_price=100000,
            )
        ]
        is_valid, error_msg = sale_engine._validate_cart(db_connection, cart)
        
        assert not is_valid
        assert "Insufficient" in error_msg
    
    def test_valid_cart_passes(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem]
    ):
        """Valid cart with sufficient stock should pass validation."""
        is_valid, error_msg = sale_engine._validate_cart(db_connection, sample_cart)
        
        assert is_valid
        assert error_msg == ""


# =============================================================================
# TOTAL CALCULATION TESTS
# =============================================================================

class TestTotalCalculation:
    """Test sale total calculations."""
    
    def test_simple_total_no_tax(
        self,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem]
    ):
        """Calculate totals without tax."""
        subtotal, tax_amount, grand_total, final_discount = \
            sale_engine._calculate_totals(sample_cart)
        
        # 2 items * Rs. 2,200 = Rs. 4,400 = 440000 cents
        assert subtotal == 440000
        assert tax_amount == 0
        assert grand_total == 440000
        assert final_discount == 0
    
    def test_total_with_tax(
        self,
        sale_engine: SaleEngine
    ):
        """Calculate totals with tax."""
        cart = [
            CartItem(
                variant_id=1,
                batch_id=1,
                quantity=1,
                unit_price=100000,  # Rs. 1,000
                tax_rate=18.0,  # 18% GST
            )
        ]
        subtotal, tax_amount, grand_total, final_discount = \
            sale_engine._calculate_totals(cart)
        
        assert subtotal == 100000
        assert tax_amount == 18000  # 18% of 100000
        assert grand_total == 118000
    
    def test_total_with_discount(
        self,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem]
    ):
        """Calculate totals with discount."""
        subtotal, tax_amount, grand_total, final_discount = \
            sale_engine._calculate_totals(sample_cart, discount_amount=50000)
        
        assert subtotal == 440000
        assert grand_total == 390000  # 440000 - 50000
        assert final_discount == 50000
    
    def test_discount_cannot_exceed_subtotal(
        self,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem]
    ):
        """Discount should be capped at subtotal."""
        subtotal, tax_amount, grand_total, final_discount = \
            sale_engine._calculate_totals(sample_cart, discount_amount=1000000)
        
        assert final_discount == 440000  # Capped at subtotal
        assert grand_total == 0
    
    def test_negative_discount_raises_error(
        self,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem]
    ):
        """Negative discount should raise assertion error."""
        with pytest.raises(AssertionError, match="Discount cannot be negative"):
            sale_engine._calculate_totals(sample_cart, discount_amount=-1000)


# =============================================================================
# STOCK DEDUCTION TESTS
# =============================================================================

class TestStockDeduction:
    """Test stock deduction logic."""
    
    def test_stock_deducted_from_variant(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_variant: dict
    ):
        """Stock should be deducted from variant quantity."""
        initial_qty = sample_variant["quantity"]
        
        sale_engine._deduct_stock(db_connection, sample_cart)
        
        cursor = db_connection.execute(
            "SELECT quantity FROM variants WHERE id = ?",
            (sample_variant["id"],)
        )
        new_qty = cursor.fetchone()["quantity"]
        
        assert new_qty == initial_qty - 2  # 2 items in cart
    
    def test_stock_deducted_from_batch(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_batch: dict
    ):
        """Stock should be deducted from batch remaining quantity."""
        initial_remaining = sample_batch["quantity_remaining"]
        
        sale_engine._deduct_stock(db_connection, sample_cart)
        
        cursor = db_connection.execute(
            "SELECT quantity_remaining FROM batches WHERE id = ?",
            (sample_batch["id"],)
        )
        new_remaining = cursor.fetchone()["quantity_remaining"]
        
        assert new_remaining == initial_remaining - 2


# =============================================================================
# FULL SALE PROCESSING TESTS
# =============================================================================

class TestProcessSale:
    """Test complete sale processing workflow."""
    
    def test_cash_sale_success(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_user: dict
    ):
        """Process a successful cash sale."""
        payment_info = PaymentInfo(
            payment_type="cash",
            paid_amount=440000,  # Exact amount
        )
        
        result = sale_engine.process_sale(
            conn=db_connection,
            cart=sample_cart,
            customer_id=None,
            user_id=sample_user["id"],
            payment_info=payment_info,
        )
        
        assert isinstance(result, SaleResult)
        assert result.grand_total == 440000
        assert result.paid_amount == 440000
        assert result.due_amount == 0
        assert result.change_amount == 0
        assert result.items_count == 1
        assert "INV-" in result.invoice_number
    
    def test_credit_sale_updates_customer_due(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_customer: dict,
        sample_user: dict
    ):
        """Credit sale should update customer's total_due."""
        payment_info = PaymentInfo(
            payment_type="credit",
            paid_amount=0,  # No payment
        )
        
        result = sale_engine.process_sale(
            conn=db_connection,
            cart=sample_cart,
            customer_id=sample_customer["id"],
            user_id=sample_user["id"],
            payment_info=payment_info,
        )
        
        assert result.due_amount == 440000
        
        # Verify customer due updated
        cursor = db_connection.execute(
            "SELECT total_due FROM customers WHERE id = ?",
            (sample_customer["id"],)
        )
        new_due = cursor.fetchone()["total_due"]
        
        assert new_due == 440000
    
    def test_partial_payment_credit_sale(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_customer: dict,
        sample_user: dict
    ):
        """Partial payment should record credit payment."""
        payment_info = PaymentInfo(
            payment_type="credit",
            paid_amount=200000,  # Partial payment
        )
        
        result = sale_engine.process_sale(
            conn=db_connection,
            cart=sample_cart,
            customer_id=sample_customer["id"],
            user_id=sample_user["id"],
            payment_info=payment_info,
        )
        
        assert result.due_amount == 240000  # 440000 - 200000
        
        # Verify credit payment recorded
        cursor = db_connection.execute(
            "SELECT amount FROM credit_payments WHERE customer_id = ?",
            (sample_customer["id"],)
        )
        payments = cursor.fetchall()
        
        assert len(payments) > 0
        assert payments[0]["amount"] == 200000
    
    def test_change_calculated_correctly(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_user: dict
    ):
        """Change should be calculated for overpayment."""
        payment_info = PaymentInfo(
            payment_type="cash",
            paid_amount=500000,  # Rs. 5,000 paid for Rs. 4,400 sale
        )
        
        result = sale_engine.process_sale(
            conn=db_connection,
            cart=sample_cart,
            customer_id=None,
            user_id=sample_user["id"],
            payment_info=payment_info,
        )
        
        assert result.change_amount == 60000  # Rs. 600 change
    
    def test_credit_sale_requires_customer(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_user: dict
    ):
        """Credit sale without customer should raise error."""
        payment_info = PaymentInfo(
            payment_type="credit",
            paid_amount=0,
        )
        
        with pytest.raises(ValueError, match="Customer required"):
            sale_engine.process_sale(
                conn=db_connection,
                cart=sample_cart,
                customer_id=None,
                user_id=sample_user["id"],
                payment_info=payment_info,
            )
    
    def test_credit_limit_exceeded(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_user: dict
    ):
        """Exceeding credit limit should raise error."""
        # Create customer with zero credit limit
        cursor = db_connection.execute(
            """INSERT INTO customers (name, phone, credit_limit, total_due)
               VALUES (?, ?, ?, ?)""",
            ("No Credit Customer", "0300-9999999", 0, 0)
        )
        customer_id = cursor.lastrowid
        db_connection.commit()
        
        payment_info = PaymentInfo(
            payment_type="credit",
            paid_amount=0,
        )
        
        with pytest.raises(ValueError, match="credit limit exceeded"):
            sale_engine.process_sale(
                conn=db_connection,
                cart=sample_cart,
                customer_id=customer_id,
                user_id=sample_user["id"],
                payment_info=payment_info,
            )
    
    def test_loyalty_points_accrued(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_customer: dict,
        sample_user: dict
    ):
        """Loyalty points should be accrued on paid amount."""
        payment_info = PaymentInfo(
            payment_type="cash",
            paid_amount=440000,
        )
        
        result = sale_engine.process_sale(
            conn=db_connection,
            cart=sample_cart,
            customer_id=sample_customer["id"],
            user_id=sample_user["id"],
            payment_info=payment_info,
        )
        
        # 1 point per Rs. 100, so Rs. 4,400 = 44 points
        expected_points = 440000 // 100 // 100
        assert result.loyalty_points_earned == expected_points
        
        # Verify customer points updated
        cursor = db_connection.execute(
            "SELECT loyalty_points FROM customers WHERE id = ?",
            (sample_customer["id"],)
        )
        new_points = cursor.fetchone()["loyalty_points"]
        
        assert new_points == expected_points
    
    def test_invoice_number_sequential(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_cart: List[CartItem],
        sample_user: dict
    ):
        """Invoice numbers should be sequential."""
        payment_info = PaymentInfo(
            payment_type="cash",
            paid_amount=440000,
        )
        
        result1 = sale_engine.process_sale(
            conn=db_connection,
            cart=sample_cart,
            customer_id=None,
            user_id=sample_user["id"],
            payment_info=payment_info,
        )
        
        result2 = sale_engine.process_sale(
            conn=db_connection,
            cart=sample_cart,
            customer_id=None,
            user_id=sample_user["id"],
            payment_info=payment_info,
        )
        
        # Extract sequence numbers
        seq1 = int(result1.invoice_number.split("-")[-1])
        seq2 = int(result2.invoice_number.split("-")[-1])
        
        assert seq2 == seq1 + 1


# =============================================================================
# TRANSACTION ATOMICITY TESTS
# =============================================================================

class TestTransactionAtomicity:
    """Test that sales are atomic (all or nothing)."""
    
    def test_rollback_on_failure(
        self,
        db_connection: sqlite3.Connection,
        sale_engine: SaleEngine,
        sample_variant: dict,
        sample_user: dict
    ):
        """Failed sale should rollback all changes."""
        # Get initial stock
        cursor = db_connection.execute(
            "SELECT quantity FROM variants WHERE id = ?",
            (sample_variant["id"],)
        )
        initial_qty = cursor.fetchone()["quantity"]
        
        # Try to sell more than available (should fail)
        cart = [
            CartItem(
                variant_id=sample_variant["id"],
                batch_id=99999,  # Invalid batch
                quantity=1000,
                unit_price=100000,
            )
        ]
        
        payment_info = PaymentInfo(
            payment_type="cash",
            paid_amount=1000000,
        )
        
        with pytest.raises(ValueError):
            sale_engine.process_sale(
                conn=db_connection,
                cart=cart,
                customer_id=None,
                user_id=sample_user["id"],
                payment_info=payment_info,
            )
        
        # Verify stock unchanged (rollback worked)
        cursor = db_connection.execute(
            "SELECT quantity FROM variants WHERE id = ?",
            (sample_variant["id"],)
        )
        final_qty = cursor.fetchone()["quantity"]
        
        assert final_qty == initial_qty


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestCreateSaleWithTransaction:
    """Test the convenience wrapper function."""
    
    def test_wrapper_creates_sale(
        self,
        db_connection: sqlite3.Connection,
        sample_cart: List[CartItem],
        sample_user: dict
    ):
        """Wrapper function should create sale successfully."""
        from database.connection import ConnectionManager
        
        # Mock connection manager for testing
        class MockManager:
            def execute_transaction(self):
                return _TransactionContext(db_connection)
        
        class _TransactionContext:
            def __init__(self, conn):
                self.conn = conn
            def __enter__(self):
                return self.conn
            def __exit__(self, *args):
                pass
        
        payment_info = PaymentInfo(
            payment_type="cash",
            paid_amount=440000,
        )
        
        result = create_sale_with_transaction(
            db_manager=MockManager(),
            cart=sample_cart,
            customer_id=None,
            user_id=sample_user["id"],
            payment_info=payment_info,
        )
        
        assert isinstance(result, SaleResult)
        assert result.grand_total == 440000