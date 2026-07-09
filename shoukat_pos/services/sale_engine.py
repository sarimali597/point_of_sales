"""
Sale Processing Engine with Atomic Transactions

This module implements the core sale processing logic for Shoukat POS.
All sale operations execute within ACID transactions to ensure data integrity.

Key Features:
- Atomic sale processing (stock deduction + sale record + customer credit)
- Support for cash, credit, and split payments
- Gift card redemption
- Loyalty points accrual
- Automatic receipt data generation
- Audit logging integration
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import sqlite3
import json
import logging

from database.models import Sale, SaleItem, Customer, Variant, Batch
from utils.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


@dataclass
class CartItem:
    """Item in the shopping cart before checkout."""
    variant_id: int
    batch_id: int
    quantity: int
    unit_price: int  # In cents
    tax_rate: float = 0.0
    
    # Computed fields
    barcode: str = ""
    size: str = ""
    color: str = ""
    style_name: str = ""
    
    @property
    def subtotal(self) -> int:
        """Calculate subtotal (quantity * unit_price) in cents."""
        return self.quantity * self.unit_price
    
    @property
    def tax_amount(self) -> int:
        """Calculate tax amount in cents."""
        if self.tax_rate <= 0:
            return 0
        return int(self.subtotal * self.tax_rate / 100)
    
    @property
    def total_amount(self) -> int:
        """Calculate total including tax in cents."""
        return self.subtotal + self.tax_amount
    
    @property
    def unit_price_rs(self) -> float:
        """Get unit price in Rupees."""
        return self.unit_price / 100.0
    
    @property
    def total_amount_rs(self) -> float:
        """Get total amount in Rupees."""
        return self.total_amount / 100.0


@dataclass
class PaymentInfo:
    """Payment information for a sale."""
    payment_type: str  # 'cash', 'credit', 'split', 'gift_card'
    paid_amount: int  # In cents
    gift_card_number: Optional[str] = None
    gift_card_pin: Optional[str] = None
    split_payments: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def paid_amount_rs(self) -> float:
        """Get paid amount in Rupees."""
        return self.paid_amount / 100.0


@dataclass
class SaleResult:
    """Result of a successful sale transaction."""
    sale_id: int
    invoice_number: str
    grand_total: int
    paid_amount: int
    due_amount: int
    change_amount: int
    items_count: int
    loyalty_points_earned: int = 0
    gift_card_balance_remaining: int = 0
    
    @property
    def grand_total_rs(self) -> float:
        """Get grand total in Rupees."""
        return self.grand_total / 100.0
    
    @property
    def paid_amount_rs(self) -> float:
        """Get paid amount in Rupees."""
        return self.paid_amount / 100.0
    
    @property
    def due_amount_rs(self) -> float:
        """Get due amount in Rupees."""
        return self.due_amount / 100.0
    
    @property
    def change_amount_rs(self) -> float:
        """Get change amount in Rupees."""
        return self.change_amount / 100.0


class SaleEngine:
    """
    Core sale processing engine with atomic transaction support.
    
    This class handles the complete sale workflow:
    1. Validate cart items and stock availability
    2. Calculate totals (subtotal, tax, discount, grand total)
    3. Process payment (cash/credit/split/gift card)
    4. Deduct stock from batches (FIFO)
    5. Create sale record and sale items
    6. Update customer credit balance (if credit sale)
    7. Accrue loyalty points
    8. Generate audit log entries
    9. Return receipt data for printing
    
    All operations execute within a single atomic transaction to ensure
    data consistency even if power fails mid-transaction.
    """
    
    def __init__(self, audit_logger: Optional[AuditLogger] = None):
        """
        Initialize the sale engine.
        
        Args:
            audit_logger: Optional audit logger for tamper detection
        """
        self.audit_logger = audit_logger or AuditLogger()
    
    def _generate_invoice_number(self, conn: sqlite3.Connection) -> str:
        """
        Generate unique invoice number for the sale.
        
        Format: INV-YYYYMMDD-XXXX where XXXX is sequential
        
        Args:
            conn: Database connection
            
        Returns:
            Unique invoice number string
        """
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"INV-{today}-"
        
        # Get last invoice number for today
        cursor = conn.execute(
            """SELECT invoice_number FROM sales 
               WHERE invoice_number LIKE ? 
               ORDER BY invoice_number DESC LIMIT 1""",
            (prefix + "%",)
        )
        result = cursor.fetchone()
        
        if result:
            # Extract sequence number and increment
            last_num = int(result[0].split("-")[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:04d}"
    
    def _validate_cart(
        self, 
        conn: sqlite3.Connection, 
        cart: List[CartItem]
    ) -> Tuple[bool, str]:
        """
        Validate all cart items have sufficient stock.
        
        Args:
            conn: Database connection
            cart: List of cart items to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        assert len(cart) > 0, "Cart cannot be empty"
        
        for item in cart:
            assert item.quantity > 0, f"Quantity must be positive for variant {item.variant_id}"
            assert item.unit_price >= 0, f"Price must be non-negative for variant {item.variant_id}"
            
            # Check variant exists and has stock
            cursor = conn.execute(
                """SELECT v.id, v.quantity, v.barcode, v.size, v.color, s.name as style_name
                   FROM variants v
                   JOIN styles s ON v.style_id = s.id
                   WHERE v.id = ?""",
                (item.variant_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                return False, f"Variant {item.variant_id} not found"
            
            if result["quantity"] < item.quantity:
                return False, (
                    f"Insufficient stock for {result['style_name']} "
                    f"({result['size']}/{result['color']}). "
                    f"Available: {result['quantity']}, Requested: {item.quantity}"
                )
            
            # Check batch exists and has remaining quantity
            cursor = conn.execute(
                """SELECT id, quantity_remaining, purchase_price, secret_code
                   FROM batches
                   WHERE id = ? AND variant_id = ?""",
                (item.batch_id, item.variant_id)
            )
            batch_result = cursor.fetchone()
            
            if not batch_result:
                return False, f"Batch {item.batch_id} not found for variant {item.variant_id}"
            
            if batch_result["quantity_remaining"] < item.quantity:
                return False, (
                    f"Insufficient quantity in batch {item.batch_id}. "
                    f"Available: {batch_result['quantity_remaining']}, "
                    f"Requested: {item.quantity}"
                )
            
            # Populate cart item with variant details
            item.barcode = result["barcode"]
            item.size = result["size"]
            item.color = result["color"]
            item.style_name = result["style_name"]
        
        return True, ""
    
    def _calculate_totals(
        self, 
        cart: List[CartItem],
        discount_amount: int = 0
    ) -> Tuple[int, int, int, int]:
        """
        Calculate sale totals from cart items.
        
        Args:
            cart: List of cart items
            discount_amount: Discount amount in cents
            
        Returns:
            Tuple of (subtotal, tax_amount, grand_total, final_discount)
        """
        assert discount_amount >= 0, "Discount cannot be negative"
        
        subtotal = sum(item.subtotal for item in cart)
        tax_amount = sum(item.tax_amount for item in cart)
        
        # Ensure discount doesn't exceed subtotal
        final_discount = min(discount_amount, subtotal)
        
        grand_total = subtotal + tax_amount - final_discount
        
        assert grand_total >= 0, "Grand total cannot be negative"
        
        return subtotal, tax_amount, grand_total, final_discount
    
    def _deduct_stock(
        self, 
        conn: sqlite3.Connection, 
        cart: List[CartItem]
    ) -> None:
        """
        Deduct stock from batches for all cart items.
        
        Uses FIFO (First-In-First-Out) inventory method by deducting
        from the specified batch.
        
        Args:
            conn: Database connection
            cart: List of cart items to process
        """
        for item in cart:
            # Deduct from variant total quantity
            conn.execute(
                """UPDATE variants 
                   SET quantity = quantity - ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (item.quantity, item.variant_id)
            )
            
            # Deduct from batch remaining quantity
            conn.execute(
                """UPDATE batches 
                   SET quantity_remaining = quantity_remaining - ?
                   WHERE id = ?""",
                (item.quantity, item.batch_id)
            )
            
            logger.debug(
                f"Deducted {item.quantity} from variant {item.variant_id}, "
                f"batch {item.batch_id}"
            )
    
    def _create_sale_record(
        self,
        conn: sqlite3.Connection,
        invoice_number: str,
        customer_id: Optional[int],
        user_id: int,
        subtotal: int,
        tax_amount: int,
        discount_amount: int,
        grand_total: int,
        payment_type: str,
        paid_amount: int,
        due_amount: int,
        change_amount: int,
        notes: Optional[str] = None
    ) -> int:
        """
        Create the main sale record.
        
        Args:
            conn: Database connection
            invoice_number: Unique invoice identifier
            customer_id: Optional customer ID for credit sales
            user_id: Cashier user ID
            subtotal: Subtotal in cents
            tax_amount: Tax amount in cents
            discount_amount: Discount in cents
            grand_total: Grand total in cents
            payment_type: Payment method
            paid_amount: Amount paid in cents
            due_amount: Amount due in cents
            change_amount: Change to return in cents
            notes: Optional notes
            
        Returns:
            Sale ID of the created record
        """
        cursor = conn.execute(
            """INSERT INTO sales (invoice_number, customer_id, user_id,
                                  subtotal, tax_amount, discount_amount,
                                  grand_total, payment_type, paid_amount,
                                  due_amount, change_amount, status, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?)""",
            (invoice_number, customer_id, user_id, subtotal, tax_amount,
             discount_amount, grand_total, payment_type, paid_amount,
             due_amount, change_amount, notes)
        )
        
        sale_id = cursor.lastrowid
        logger.info(f"Created sale {sale_id} with invoice {invoice_number}")
        
        return sale_id  # type: ignore
    
    def _create_sale_items(
        self,
        conn: sqlite3.Connection,
        sale_id: int,
        cart: List[CartItem]
    ) -> List[int]:
        """
        Create sale item records for each cart item.
        
        Args:
            conn: Database connection
            sale_id: Parent sale ID
            cart: List of cart items
            
        Returns:
            List of created sale item IDs
        """
        item_ids = []
        
        for item in cart:
            cursor = conn.execute(
                """INSERT INTO sale_items (sale_id, variant_id, batch_id,
                                           quantity, unit_price, tax_amount,
                                           total_amount)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (sale_id, item.variant_id, item.batch_id, item.quantity,
                 item.unit_price, item.tax_amount, item.total_amount)
            )
            item_ids.append(cursor.lastrowid)
        
        logger.debug(f"Created {len(item_ids)} sale items for sale {sale_id}")
        return item_ids  # type: ignore
    
    def _update_customer_credit(
        self,
        conn: sqlite3.Connection,
        customer_id: int,
        sale_id: int,
        due_amount: int,
        paid_amount: int
    ) -> None:
        """
        Update customer credit balance for credit sales.
        
        Args:
            conn: Database connection
            customer_id: Customer ID
            sale_id: Sale ID
            due_amount: Amount due in cents
            paid_amount: Amount paid in cents
        """
        if due_amount > 0:
            # Add to customer's total_due
            conn.execute(
                """UPDATE customers 
                   SET total_due = total_due + ?, 
                       total_purchases = total_purchases + ?,
                       last_purchase_date = CURRENT_DATE,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (due_amount, due_amount + paid_amount, customer_id)
            )
            
            # Record credit payment if partial payment was made
            if paid_amount > 0:
                conn.execute(
                    """INSERT INTO credit_payments 
                       (customer_id, sale_id, amount, payment_method, user_id)
                       VALUES (?, ?, ?, 'partial', NULL)""",
                    (customer_id, sale_id, paid_amount)
                )
            
            logger.info(
                f"Updated customer {customer_id} credit: +{due_amount} due"
            )
        else:
            # Full payment - update total purchases
            conn.execute(
                """UPDATE customers 
                   SET total_purchases = total_purchases + ?,
                       last_purchase_date = CURRENT_DATE,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (paid_amount, customer_id)
            )
    
    def _accrue_loyalty_points(
        self,
        conn: sqlite3.Connection,
        customer_id: int,
        sale_id: int,
        grand_total: int
    ) -> int:
        """
        Accrue loyalty points for the sale.
        
        Points calculation: 1 point per Rs. 100 spent
        
        Args:
            conn: Database connection
            customer_id: Customer ID
            sale_id: Sale ID
            grand_total: Grand total in cents
            
        Returns:
            Points earned
        """
        # 1 point per Rs. 100 (10000 cents)
        points_per_rupee = 1
        rupees_per_point = 100
        
        points_earned = (grand_total // 100) // rupees_per_point
        
        if points_earned > 0:
            # Get current balance
            cursor = conn.execute(
                "SELECT loyalty_points FROM customers WHERE id = ?",
                (customer_id,)
            )
            result = cursor.fetchone()
            current_balance = result["loyalty_points"] if result else 0
            
            new_balance = current_balance + points_earned
            
            # Update customer points
            conn.execute(
                """UPDATE customers 
                   SET loyalty_points = ?, updated_at = CURRENT_TIMESTAMP
                   WHERE id = ?""",
                (new_balance, customer_id)
            )
            
            # Record loyalty transaction
            conn.execute(
                """INSERT INTO loyalty_transactions 
                   (customer_id, sale_id, transaction_type, points, 
                    balance_after, description)
                   VALUES (?, ?, 'earned', ?, ?, ?)""",
                (customer_id, sale_id, points_earned, new_balance,
                 f"Points earned on sale {sale_id}")
            )
            
            logger.info(
                f"Accrued {points_earned} loyalty points for customer {customer_id}"
            )
        
        return points_earned
    
    def _validate_gift_card(
        self,
        conn: sqlite3.Connection,
        card_number: str,
        pin: str
    ) -> Tuple[bool, int, str]:
        """
        Validate gift card and return available balance.
        
        Args:
            conn: Database connection
            card_number: Gift card number
            pin: Gift card PIN
            
        Returns:
            Tuple of (is_valid, balance, error_message)
        """
        import bcrypt
        
        cursor = conn.execute(
            """SELECT id, balance, pin_hash, status, expiry_date
               FROM gift_cards
               WHERE card_number = ?""",
            (card_number,)
        )
        result = cursor.fetchone()
        
        if not result:
            return False, 0, "Gift card not found"
        
        if result["status"] != "active":
            return False, 0, f"Gift card is {result['status']}"
        
        # Verify PIN
        if not bcrypt.checkpw(pin.encode(), result["pin_hash"].encode()):
            return False, 0, "Invalid gift card PIN"
        
        # Check expiry
        if result["expiry_date"]:
            expiry = datetime.strptime(result["expiry_date"], "%Y-%m-%d")
            if expiry < datetime.now():
                # Mark as expired
                conn.execute(
                    """UPDATE gift_cards 
                       SET status = 'expired' 
                       WHERE id = ?""",
                    (result["id"],)
                )
                return False, 0, "Gift card has expired"
        
        return True, result["balance"], ""
    
    def _redeem_gift_card(
        self,
        conn: sqlite3.Connection,
        card_number: str,
        amount: int
    ) -> int:
        """
        Redeem amount from gift card.
        
        Args:
            conn: Database connection
            card_number: Gift card number
            amount: Amount to redeem in cents
            
        Returns:
            Remaining balance on gift card
        """
        cursor = conn.execute(
            """SELECT id, balance FROM gift_cards 
               WHERE card_number = ?""",
            (card_number,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise ValueError("Gift card not found")
        
        new_balance = result["balance"] - amount
        
        if new_balance < 0:
            raise ValueError("Insufficient gift card balance")
        
        conn.execute(
            """UPDATE gift_cards 
               SET balance = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (new_balance, result["id"])
        )
        
        # If balance is zero, mark as used
        if new_balance == 0:
            conn.execute(
                """UPDATE gift_cards 
                   SET status = 'used' 
                   WHERE id = ?""",
                (result["id"],)
            )
        
        logger.info(
            f"Redeemed {amount} from gift card {card_number}, "
            f"remaining: {new_balance}"
        )
        
        return new_balance
    
    def process_sale(
        self,
        conn: sqlite3.Connection,
        cart: List[CartItem],
        customer_id: Optional[int],
        user_id: int,
        payment_info: PaymentInfo,
        discount_amount: int = 0,
        notes: Optional[str] = None
    ) -> SaleResult:
        """
        Process a complete sale transaction atomically.
        
        This is the main entry point for sale processing. It performs
        all steps within a single transaction to ensure data integrity.
        
        Args:
            conn: Database connection (must be within a transaction)
            cart: List of cart items to purchase
            customer_id: Optional customer ID for credit tracking
            user_id: Cashier user ID
            payment_info: Payment information
            discount_amount: Discount amount in cents
            notes: Optional notes for the sale
            
        Returns:
            SaleResult with sale details
            
        Raises:
            ValueError: If validation fails (insufficient stock, etc.)
            RuntimeError: If transaction fails
        """
        # ==================== VALIDATION PHASE ====================
        
        # Validate cart is not empty
        assert len(cart) > 0, "Cart cannot be empty"
        
        # Validate all items have stock
        is_valid, error_msg = self._validate_cart(conn, cart)
        if not is_valid:
            raise ValueError(error_msg)
        
        # ==================== CALCULATION PHASE ====================
        
        # Calculate totals
        subtotal, tax_amount, grand_total, final_discount = \
            self._calculate_totals(cart, discount_amount)
        
        # Determine payment amounts
        paid_amount = payment_info.paid_amount
        payment_type = payment_info.payment_type
        
        # Handle gift card payment
        gift_card_remaining = 0
        if payment_type == "gift_card" and payment_info.gift_card_number:
            # Validate gift card
            is_valid, balance, error_msg = self._validate_gift_card(
                conn, 
                payment_info.gift_card_number,
                payment_info.gift_card_pin or ""
            )
            if not is_valid:
                raise ValueError(error_msg)
            
            if balance < grand_total:
                raise ValueError(
                    f"Insufficient gift card balance. "
                    f"Available: Rs. {balance/100:.2f}, "
                    f"Required: Rs. {grand_total/100:.2f}"
                )
            
            paid_amount = grand_total
        
        # Calculate due and change
        if grand_total > paid_amount:
            # Credit sale or insufficient payment
            due_amount = grand_total - paid_amount
            change_amount = 0
            
            # If no customer specified for credit sale, require one
            if due_amount > 0 and customer_id is None:
                raise ValueError(
                    "Customer required for credit sales. "
                    "Please select or create a customer."
                )
            
            # Verify customer credit limit
            if customer_id:
                cursor = conn.execute(
                    """SELECT credit_limit, total_due 
                       FROM customers WHERE id = ?""",
                    (customer_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    available_credit = result["credit_limit"] - result["total_due"]
                    if due_amount > available_credit:
                        raise ValueError(
                            f"Customer credit limit exceeded. "
                            f"Available: Rs. {available_credit/100:.2f}, "
                            f"Required: Rs. {due_amount/100:.2f}"
                        )
        else:
            # Full payment - calculate change
            due_amount = 0
            change_amount = paid_amount - grand_total
        
        # ==================== TRANSACTION PHASE ====================
        
        # Generate invoice number
        invoice_number = self._generate_invoice_number(conn)
        
        # Deduct stock from inventory
        self._deduct_stock(conn, cart)
        
        # Create sale record
        sale_id = self._create_sale_record(
            conn,
            invoice_number,
            customer_id,
            user_id,
            subtotal,
            tax_amount,
            final_discount,
            grand_total,
            payment_type,
            paid_amount,
            due_amount,
            change_amount,
            notes
        )
        
        # Create sale items
        self._create_sale_items(conn, sale_id, cart)
        
        # Update customer credit if applicable
        if customer_id:
            self._update_customer_credit(
                conn, customer_id, sale_id, due_amount, paid_amount
            )
            
            # Accrue loyalty points (only for paid amount)
            points_earned = self._accrue_loyalty_points(
                conn, customer_id, sale_id, paid_amount
            )
        else:
            points_earned = 0
        
        # Redeem gift card if used
        if payment_type == "gift_card" and payment_info.gift_card_number:
            gift_card_remaining = self._redeem_gift_card(
                conn,
                payment_info.gift_card_number,
                grand_total
            )
        
        # ==================== AUDIT LOGGING ====================
        
        self.audit_logger.log_action(
            conn=conn,
            table_name="sales",
            record_id=sale_id,
            action="INSERT",
            new_values={
                "invoice_number": invoice_number,
                "customer_id": customer_id,
                "grand_total": grand_total,
                "payment_type": payment_type,
                "items_count": len(cart),
            },
            user_id=user_id
        )
        
        # ==================== RETURN RESULT ====================
        
        result = SaleResult(
            sale_id=sale_id,
            invoice_number=invoice_number,
            grand_total=grand_total,
            paid_amount=paid_amount,
            due_amount=due_amount,
            change_amount=change_amount,
            items_count=len(cart),
            loyalty_points_earned=points_earned,
            gift_card_balance_remaining=gift_card_remaining
        )
        
        logger.info(
            f"Sale completed: {invoice_number}, "
            f"Total: Rs. {grand_total/100:.2f}, "
            f"Items: {len(cart)}"
        )
        
        return result
    
    def get_sale_for_receipt(
        self, 
        conn: sqlite3.Connection, 
        sale_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve sale data formatted for receipt printing.
        
        Args:
            conn: Database connection
            sale_id: Sale ID to retrieve
            
        Returns:
            Dictionary with sale and item data for receipt generation
        """
        # Get sale header
        cursor = conn.execute(
            """SELECT s.*, c.name as customer_name, c.phone as customer_phone,
                      u.full_name as cashier_name
               FROM sales s
               LEFT JOIN customers c ON s.customer_id = c.id
               LEFT JOIN users u ON s.user_id = u.id
               WHERE s.id = ?""",
            (sale_id,)
        )
        sale_row = cursor.fetchone()
        
        if not sale_row:
            return None
        
        # Get sale items with variant details
        cursor = conn.execute(
            """SELECT si.*, v.barcode, v.size, v.color, s.name as style_name
               FROM sale_items si
               JOIN variants v ON si.variant_id = v.id
               JOIN styles s ON v.style_id = s.id
               WHERE si.sale_id = ?""",
            (sale_id,)
        )
        items = [dict(row) for row in cursor.fetchall()]
        
        return {
            "sale": dict(sale_row),
            "items": items,
        }


# Convenience function for creating sale with automatic transaction
def create_sale_with_transaction(
    db_manager: Any,  # ConnectionManager type
    cart: List[CartItem],
    customer_id: Optional[int],
    user_id: int,
    payment_info: PaymentInfo,
    discount_amount: int = 0,
    notes: Optional[str] = None
) -> SaleResult:
    """
    Create a sale with automatic transaction management.
    
    This is a convenience wrapper that handles the transaction context
    automatically. Use this when you don't need to combine the sale
    with other database operations.
    
    Args:
        db_manager: ConnectionManager instance
        cart: List of cart items
        customer_id: Optional customer ID
        user_id: Cashier user ID
        payment_info: Payment information
        discount_amount: Discount in cents
        notes: Optional notes
        
    Returns:
        SaleResult with sale details
    """
    engine = SaleEngine()
    
    with db_manager.execute_transaction() as conn:
        result = engine.process_sale(
            conn=conn,
            cart=cart,
            customer_id=customer_id,
            user_id=user_id,
            payment_info=payment_info,
            discount_amount=discount_amount,
            notes=notes
        )
    
    return result