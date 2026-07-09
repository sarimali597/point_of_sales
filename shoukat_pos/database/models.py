"""
Database Models - Dataclass Entities

This module defines dataclass entities for all database tables.
These classes provide type-safe, immutable representations of database records.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


# =============================================================================
# USER MODELS
# =============================================================================

@dataclass
class User:
    """User account model."""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: str = "cashier"
    phone: Optional[str] = None
    is_active: bool = True
    last_login_at: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "phone": self.phone,
            "is_active": self.is_active,
            "last_login_at": self.last_login_at,
            "created_at": self.created_at,
        }


# =============================================================================
# PRODUCT MODELS (Style-Variant-Batch Architecture)
# =============================================================================

@dataclass
class Category:
    """Product category model."""
    id: Optional[int] = None
    name: str = ""
    code: str = ""
    description: Optional[str] = None
    tax_rate: float = 0.0
    parent_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Style:
    """
    Style model - represents a product design/style.
    
    This is the parent level in the style-variant-batch hierarchy.
    A style can have multiple variants (size-color combinations).
    """
    id: Optional[int] = None
    style_code: str = ""
    name: str = ""
    category_id: int = 0
    description: Optional[str] = None
    base_sale_price: int = 0  # In cents
    tax_rate: float = 0.0
    season: Optional[str] = None
    image_path: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @property
    def sale_price_rs(self) -> float:
        """Get sale price in Rupees (converts from cents)."""
        return self.base_sale_price / 100.0


@dataclass
class Variant:
    """
    Variant model - represents a specific size-color combination.
    
    This is the sellable SKU level. Each variant has a unique barcode
    and tracks its own stock quantity.
    """
    id: Optional[int] = None
    style_id: int = 0
    size: str = ""
    color: str = ""
    barcode: str = ""
    quantity: int = 0
    reorder_point: int = 5
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Computed fields (not stored in database)
    style_name: Optional[str] = None
    category_name: Optional[str] = None
    
    @property
    def is_low_stock(self) -> bool:
        """Check if stock is at or below reorder point."""
        return self.quantity <= self.reorder_point
    
    @property
    def is_out_of_stock(self) -> bool:
        """Check if stock is zero."""
        return self.quantity == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "style_id": self.style_id,
            "style_name": self.style_name,
            "size": self.size,
            "color": self.color,
            "barcode": self.barcode,
            "quantity": self.quantity,
            "reorder_point": self.reorder_point,
            "is_low_stock": self.is_low_stock,
            "is_out_of_stock": self.is_out_of_stock,
        }


@dataclass
class Batch:
    """
    Batch model - represents a purchase batch with cost tracking.
    
    Batches enable FIFO (First-In-First-Out) inventory valuation and
    secret code encoding of purchase prices.
    """
    id: Optional[int] = None
    variant_id: int = 0
    purchase_price: int = 0  # In cents
    secret_code: str = ""
    quantity_received: int = 0
    quantity_remaining: int = 0
    vendor_id: Optional[int] = None
    bilty_no: Optional[str] = None
    bill_no: Optional[str] = None
    date_received: Optional[str] = None
    created_at: Optional[str] = None
    
    @property
    def purchase_price_rs(self) -> float:
        """Get purchase price in Rupees (converts from cents)."""
        return self.purchase_price / 100.0


# =============================================================================
# VENDOR MODELS
# =============================================================================

@dataclass
class Vendor:
    """Vendor/supplier model."""
    id: Optional[int] = None
    name: str = ""
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    gstin: Optional[str] = None
    balance_due: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# =============================================================================
# CUSTOMER MODELS
# =============================================================================

@dataclass
class Customer:
    """Customer model with credit tracking."""
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    email: Optional[str] = None
    address: Optional[str] = None
    total_purchases: int = 0
    total_paid: int = 0
    total_due: int = 0
    credit_limit: int = 0
    loyalty_points: int = 0
    last_purchase_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @property
    def available_credit(self) -> int:
        """Calculate remaining credit limit."""
        return max(0, self.credit_limit - self.total_due)
    
    @property
    def can_take_credit(self) -> bool:
        """Check if customer has available credit."""
        return self.available_credit > 0


# =============================================================================
# SALE MODELS
# =============================================================================

@dataclass
class SaleItem:
    """Individual item in a sale."""
    id: Optional[int] = None
    sale_id: int = 0
    variant_id: int = 0
    batch_id: Optional[int] = None
    quantity: int = 0
    unit_price: int = 0  # In cents
    tax_amount: int = 0
    total_amount: int = 0
    created_at: Optional[str] = None
    
    # Computed fields
    variant_barcode: Optional[str] = None
    variant_size: Optional[str] = None
    variant_color: Optional[str] = None
    style_name: Optional[str] = None
    
    @property
    def unit_price_rs(self) -> float:
        """Get unit price in Rupees."""
        return self.unit_price / 100.0
    
    @property
    def total_amount_rs(self) -> float:
        """Get total amount in Rupees."""
        return self.total_amount / 100.0


@dataclass
class Sale:
    """Complete sale transaction."""
    id: Optional[int] = None
    invoice_number: str = ""
    sale_date: Optional[str] = None
    customer_id: Optional[int] = None
    user_id: Optional[int] = None
    subtotal: int = 0
    tax_amount: int = 0
    discount_amount: int = 0
    grand_total: int = 0
    payment_type: str = "cash"  # cash, credit, split
    paid_amount: int = 0
    due_amount: int = 0
    change_amount: int = 0
    status: str = "completed"  # completed, held, voided
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Computed fields
    customer_name: Optional[str] = None
    cashier_name: Optional[str] = None
    items: List[SaleItem] = field(default_factory=list)
    
    @property
    def subtotal_rs(self) -> float:
        """Get subtotal in Rupees."""
        return self.subtotal / 100.0
    
    @property
    def grand_total_rs(self) -> float:
        """Get grand total in Rupees."""
        return self.grand_total / 100.0
    
    @property
    def paid_amount_rs(self) -> float:
        """Get paid amount in Rupees."""
        return self.paid_amount / 100.0
    
    @property
    def is_credit_sale(self) -> bool:
        """Check if this is a credit sale."""
        return self.payment_type == "credit" or self.due_amount > 0


# =============================================================================
# RETURN & EXCHANGE MODELS
# =============================================================================

@dataclass
class ReturnItem:
    """Individual item in a return."""
    id: Optional[int] = None
    return_id: int = 0
    sale_item_id: int = 0
    variant_id: int = 0
    quantity: int = 0
    unit_price: int = 0
    total_amount: int = 0
    created_at: Optional[str] = None


@dataclass
class Return:
    """Return transaction."""
    id: Optional[int] = None
    return_number: str = ""
    sale_id: int = 0
    return_date: Optional[str] = None
    user_id: Optional[int] = None
    reason: str = ""
    refund_amount: int = 0
    refund_type: str = "cash"
    status: str = "completed"
    notes: Optional[str] = None
    created_at: Optional[str] = None
    
    items: List[ReturnItem] = field(default_factory=list)


@dataclass
class Exchange:
    """Exchange transaction (variant swap)."""
    id: Optional[int] = None
    exchange_number: str = ""
    original_sale_id: int = 0
    new_sale_id: Optional[int] = None
    exchange_date: Optional[str] = None
    user_id: Optional[int] = None
    reason: str = ""
    price_difference: int = 0
    payment_status: str = "settled"
    notes: Optional[str] = None
    created_at: Optional[str] = None


# =============================================================================
# HELD SALE MODEL
# =============================================================================

@dataclass
class HeldSale:
    """Temporarily held sale transaction."""
    id: Optional[int] = None
    hold_number: str = ""
    sale_data: str = ""  # JSON string
    customer_id: Optional[int] = None
    user_id: Optional[int] = None
    held_at: Optional[str] = None
    resumed_at: Optional[str] = None
    status: str = "held"


# =============================================================================
# CREDIT PAYMENT MODEL
# =============================================================================

@dataclass
class CreditPayment:
    """Payment toward customer credit balance."""
    id: Optional[int] = None
    customer_id: int = 0
    sale_id: Optional[int] = None
    payment_date: Optional[str] = None
    amount: int = 0
    payment_method: str = "cash"
    reference_no: Optional[str] = None
    notes: Optional[str] = None
    user_id: Optional[int] = None
    created_at: Optional[str] = None
    
    @property
    def amount_rs(self) -> float:
        """Get amount in Rupees."""
        return self.amount / 100.0


# =============================================================================
# AUDIT LOG MODEL
# =============================================================================

@dataclass
class AuditLog:
    """Audit trail entry for tamper detection."""
    id: Optional[int] = None
    table_name: str = ""
    record_id: int = 0
    action: str = ""  # INSERT, UPDATE, DELETE
    old_values: Optional[str] = None  # JSON
    new_values: Optional[str] = None  # JSON
    user_id: Optional[int] = None
    timestamp: Optional[str] = None
    hmac_hash: str = ""


# =============================================================================
# SETTINGS MODEL
# =============================================================================

@dataclass
class Setting:
    """Application setting key-value pair."""
    id: Optional[int] = None
    key: str = ""
    value: str = ""
    type: str = "text"  # text, integer, real, boolean, json
    description: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[int] = None


# =============================================================================
# GIFT CARD MODEL
# =============================================================================

@dataclass
class GiftCard:
    """Gift card with balance tracking."""
    id: Optional[int] = None
    card_number: str = ""
    pin_hash: str = ""
    balance: int = 0
    initial_amount: int = 0
    issued_date: Optional[str] = None
    expiry_date: Optional[str] = None
    customer_id: Optional[int] = None
    status: str = "active"  # active, used, expired, void
    created_at: Optional[str] = None


# =============================================================================
# LOYALTY TRANSACTION MODEL
# =============================================================================

@dataclass
class LoyaltyTransaction:
    """Loyalty points accrual/redemption record."""
    id: Optional[int] = None
    customer_id: int = 0
    sale_id: Optional[int] = None
    transaction_type: str = ""  # earned, redeemed, adjusted
    points: int = 0
    balance_after: int = 0
    description: Optional[str] = None
    created_at: Optional[str] = None
