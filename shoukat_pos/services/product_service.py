"""Product service for managing styles, variants, and batches.

This module provides business logic for product CRUD operations,
variant matrix management, and batch tracking.
"""

from typing import Optional, List, Dict, Tuple, Any
from dataclasses import dataclass, asdict
import sqlite3
import logging

logger = logging.getLogger(__name__)


@dataclass
class StyleData:
    """Data class for style information."""
    style_code: str
    name: str
    category_id: int
    description: Optional[str] = None
    base_sale_price: int = 0  # In cents
    tax_rate: float = 0.0
    season: Optional[str] = None


@dataclass
class VariantData:
    """Data class for variant information."""
    style_id: int
    size: str
    color: str
    barcode: str
    quantity: int = 0
    reorder_point: int = 5


@dataclass
class BatchData:
    """Data class for batch information."""
    variant_id: int
    purchase_price: int  # In cents
    secret_code: str
    quantity_received: int
    quantity_remaining: int
    vendor_id: Optional[int] = None
    bilty_no: Optional[str] = None
    bill_no: Optional[str] = None
    date_received: Optional[str] = None


class ProductService:
    """Service for managing products (styles, variants, batches)."""

    def __init__(self):
        """Initialize the product service."""
        pass

    # ==================== STYLE OPERATIONS ====================

    def create_style(self, conn: sqlite3.Connection, style_data: StyleData) -> int:
        """Create a new style.

        Args:
            conn: Database connection
            style_data: StyleData object with style information

        Returns:
            The ID of the newly created style

        Raises:
            sqlite3.IntegrityError: If style_code already exists
        """
        assert isinstance(style_data, StyleData), "style_data must be StyleData"
        assert style_data.style_code, "style_code is required"
        assert style_data.name, "name is required"
        assert style_data.category_id > 0, "category_id must be positive"
        assert style_data.base_sale_price >= 0, "base_sale_price must be non-negative"

        cursor = conn.execute(
            """
            INSERT INTO styles (style_code, name, category_id, description,
                               base_sale_price, tax_rate, season)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                style_data.style_code,
                style_data.name,
                style_data.category_id,
                style_data.description,
                style_data.base_sale_price,
                style_data.tax_rate,
                style_data.season,
            ),
        )
        return cursor.lastrowid

    def get_style(self, conn: sqlite3.Connection, style_id: int) -> Optional[Dict[str, Any]]:
        """Get a style by ID.

        Args:
            conn: Database connection
            style_id: The style ID

        Returns:
            Dictionary with style data or None if not found
        """
        assert style_id > 0, "style_id must be positive"

        cursor = conn.execute(
            "SELECT * FROM styles WHERE id = ?",
            (style_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_styles(
        self,
        conn: sqlite3.Connection,
        category_id: Optional[int] = None,
        search_term: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get all styles with optional filtering.

        Args:
            conn: Database connection
            category_id: Filter by category (optional)
            search_term: Search in style name/code (optional)

        Returns:
            List of style dictionaries
        """
        assert category_id is None or category_id > 0, "category_id must be positive if provided"

        query = "SELECT * FROM styles WHERE 1=1"
        params: List[Any] = []

        if category_id:
            query += " AND category_id = ?"
            params.append(category_id)

        if search_term:
            assert isinstance(search_term, str), "search_term must be string"
            query += " AND (name LIKE ? OR style_code LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])

        query += " ORDER BY name"

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def update_style(
        self,
        conn: sqlite3.Connection,
        style_id: int,
        updates: Dict[str, Any],
    ) -> bool:
        """Update a style.

        Args:
            conn: Database connection
            style_id: The style ID to update
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        assert style_id > 0, "style_id must be positive"
        assert isinstance(updates, dict), "updates must be a dict"

        if not updates:
            return False

        allowed_fields = {"name", "category_id", "description", "base_sale_price", "tax_rate", "season"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}

        if not filtered_updates:
            logger.warning(f"No valid fields to update for style {style_id}")
            return False

        set_clause = ", ".join(f"{field} = ?" for field in filtered_updates.keys())
        values = list(filtered_updates.values()) + [style_id]

        cursor = conn.execute(
            f"UPDATE styles SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            values,
        )
        return cursor.rowcount > 0

    def delete_style(self, conn: sqlite3.Connection, style_id: int) -> bool:
        """Delete a style (and its variants via cascade).

        Args:
            conn: Database connection
            style_id: The style ID to delete

        Returns:
            True if deleted, False if not found or has dependent records
        """
        assert style_id > 0, "style_id must be positive"

        try:
            cursor = conn.execute("DELETE FROM styles WHERE id = ?", (style_id,))
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            logger.warning(f"Cannot delete style {style_id}: {e}")
            return False

    # ==================== VARIANT OPERATIONS ====================

    def create_variant(self, conn: sqlite3.Connection, variant_data: VariantData) -> int:
        """Create a new variant.

        Args:
            conn: Database connection
            variant_data: VariantData object

        Returns:
            The ID of the newly created variant

        Raises:
            sqlite3.IntegrityError: If barcode already exists or duplicate size/color
        """
        assert isinstance(variant_data, VariantData), "variant_data must be VariantData"
        assert variant_data.style_id > 0, "style_id must be positive"
        assert variant_data.size, "size is required"
        assert variant_data.color, "color is required"
        assert variant_data.barcode, "barcode is required"
        assert variant_data.quantity >= 0, "quantity must be non-negative"

        cursor = conn.execute(
            """
            INSERT INTO variants (style_id, size, color, barcode, quantity, reorder_point)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                variant_data.style_id,
                variant_data.size,
                variant_data.color,
                variant_data.barcode,
                variant_data.quantity,
                variant_data.reorder_point,
            ),
        )
        return cursor.lastrowid

    def create_variants_batch(
        self,
        conn: sqlite3.Connection,
        variants: List[VariantData],
    ) -> List[int]:
        """Create multiple variants in a single transaction.

        Args:
            conn: Database connection
            variants: List of VariantData objects

        Returns:
            List of created variant IDs
        """
        assert isinstance(variants, list), "variants must be a list"
        assert len(variants) > 0, "variants list cannot be empty"

        ids = []
        for variant in variants:
            variant_id = self.create_variant(conn, variant)
            ids.append(variant_id)
        return ids

    def get_variant(self, conn: sqlite3.Connection, variant_id: int) -> Optional[Dict[str, Any]]:
        """Get a variant by ID.

        Args:
            conn: Database connection
            variant_id: The variant ID

        Returns:
            Dictionary with variant data or None if not found
        """
        assert variant_id > 0, "variant_id must be positive"

        cursor = conn.execute(
            """
            SELECT v.*, s.name as style_name, s.style_code
            FROM variants v
            JOIN styles s ON v.style_id = s.id
            WHERE v.id = ?
            """,
            (variant_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_variant_by_barcode(
        self,
        conn: sqlite3.Connection,
        barcode: str,
    ) -> Optional[Dict[str, Any]]:
        """Get a variant by barcode.

        Args:
            conn: Database connection
            barcode: The barcode to search

        Returns:
            Dictionary with variant data or None if not found
        """
        assert barcode, "barcode is required"

        cursor = conn.execute(
            """
            SELECT v.*, s.name as style_name, s.style_code, s.base_sale_price
            FROM variants v
            JOIN styles s ON v.style_id = s.id
            WHERE v.barcode = ?
            """,
            (barcode,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_variants_by_style(
        self,
        conn: sqlite3.Connection,
        style_id: int,
    ) -> List[Dict[str, Any]]:
        """Get all variants for a style.

        Args:
            conn: Database connection
            style_id: The style ID

        Returns:
            List of variant dictionaries
        """
        assert style_id > 0, "style_id must be positive"

        cursor = conn.execute(
            """
            SELECT v.*, s.name as style_name
            FROM variants v
            JOIN styles s ON v.style_id = s.id
            WHERE v.style_id = ?
            ORDER BY v.size, v.color
            """,
            (style_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_variant_matrix(
        self,
        conn: sqlite3.Connection,
        style_id: int,
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get variant matrix as size x color grid.

        Args:
            conn: Database connection
            style_id: The style ID

        Returns:
            Nested dict: {size: {color: variant_data}}
        """
        assert style_id > 0, "style_id must be positive"

        variants = self.get_variants_by_style(conn, style_id)
        matrix: Dict[str, Dict[str, Dict[str, Any]]] = {}

        for v in variants:
            size = v["size"]
            color = v["color"]
            if size not in matrix:
                matrix[size] = {}
            matrix[size][color] = v

        return matrix

    def update_variant_quantity(
        self,
        conn: sqlite3.Connection,
        variant_id: int,
        quantity_change: int,
    ) -> bool:
        """Update variant quantity (positive or negative change).

        Args:
            conn: Database connection
            variant_id: The variant ID
            quantity_change: Amount to add (positive) or subtract (negative)

        Returns:
            True if updated successfully
        """
        assert variant_id > 0, "variant_id must be positive"
        assert isinstance(quantity_change, int), "quantity_change must be int"

        cursor = conn.execute(
            """
            UPDATE variants
            SET quantity = quantity + ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (quantity_change, variant_id),
        )
        return cursor.rowcount > 0

    def search_variants(
        self,
        conn: sqlite3.Connection,
        search_term: str,
        category_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search variants by barcode, style name, size, or color.

        Args:
            conn: Database connection
            search_term: Search term
            category_id: Optional category filter

        Returns:
            List of matching variant dictionaries
        """
        assert search_term, "search_term is required"

        query = """
            SELECT v.*, s.name as style_name, s.style_code, c.name as category_name
            FROM variants v
            JOIN styles s ON v.style_id = s.id
            JOIN categories c ON s.category_id = c.id
            WHERE v.barcode LIKE ? OR s.name LIKE ? OR v.size LIKE ? OR v.color LIKE ?
        """
        params = [f"%{search_term}%"] * 4

        if category_id:
            query += " AND s.category_id = ?"
            params.append(category_id)

        query += " ORDER BY s.name, v.size, v.color"

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    # ==================== BATCH OPERATIONS ====================

    def create_batch(self, conn: sqlite3.Connection, batch_data: BatchData) -> int:
        """Create a new batch.

        Args:
            conn: Database connection
            batch_data: BatchData object

        Returns:
            The ID of the newly created batch
        """
        assert isinstance(batch_data, BatchData), "batch_data must be BatchData"
        assert batch_data.variant_id > 0, "variant_id must be positive"
        assert batch_data.purchase_price >= 0, "purchase_price must be non-negative"
        assert batch_data.secret_code, "secret_code is required"
        assert batch_data.quantity_received > 0, "quantity_received must be positive"
        assert (
            batch_data.quantity_remaining <= batch_data.quantity_received
        ), "quantity_remaining cannot exceed quantity_received"

        cursor = conn.execute(
            """
            INSERT INTO batches (variant_id, purchase_price, secret_code,
                                quantity_received, quantity_remaining,
                                vendor_id, bilty_no, bill_no, date_received)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_data.variant_id,
                batch_data.purchase_price,
                batch_data.secret_code,
                batch_data.quantity_received,
                batch_data.quantity_remaining,
                batch_data.vendor_id,
                batch_data.bilty_no,
                batch_data.bill_no,
                batch_data.date_received,
            ),
        )
        return cursor.lastrowid

    def get_batches_for_variant(
        self,
        conn: sqlite3.Connection,
        variant_id: int,
    ) -> List[Dict[str, Any]]:
        """Get all batches for a variant (FIFO order).

        Args:
            conn: Database connection
            variant_id: The variant ID

        Returns:
            List of batch dictionaries ordered by date_received
        """
        assert variant_id > 0, "variant_id must be positive"

        cursor = conn.execute(
            """
            SELECT b.*, v.barcode, s.name as style_name
            FROM batches b
            JOIN variants v ON b.variant_id = v.id
            JOIN styles s ON v.style_id = s.id
            WHERE b.variant_id = ?
            ORDER BY b.date_received ASC, b.id ASC
            """,
            (variant_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def deduct_from_batch(
        self,
        conn: sqlite3.Connection,
        variant_id: int,
        quantity_to_deduct: int,
    ) -> List[Tuple[int, int]]:
        """Deduct quantity from batches using FIFO.

        Args:
            conn: Database connection
            variant_id: The variant ID
            quantity_to_deduct: Quantity to deduct

        Returns:
            List of (batch_id, quantity_deducted) tuples

        Raises:
            ValueError: If insufficient stock in batches
        """
        assert variant_id > 0, "variant_id must be positive"
        assert quantity_to_deduct > 0, "quantity_to_deduct must be positive"

        batches = self.get_batches_for_variant(conn, variant_id)
        remaining = quantity_to_deduct
        deductions: List[Tuple[int, int]] = []

        for batch in batches:
            if remaining <= 0:
                break

            available = batch["quantity_remaining"]
            if available > 0:
                deduct = min(available, remaining)
                batch_id = batch["id"]

                conn.execute(
                    """
                    UPDATE batches
                    SET quantity_remaining = quantity_remaining - ?
                    WHERE id = ?
                    """,
                    (deduct, batch_id),
                )
                deductions.append((batch_id, deduct))
                remaining -= deduct

        if remaining > 0:
            raise ValueError(
                f"Insufficient stock for variant {variant_id}. "
                f"Need {quantity_to_deduct}, only {quantity_to_deduct - remaining} available."
            )

        return deductions

    # ==================== UTILITY METHODS ====================

    def generate_style_code(
        self,
        conn: sqlite3.Connection,
        category_code: str,
    ) -> str:
        """Generate a unique style code.

        Args:
            conn: Database connection
            category_code: Category code prefix (e.g., 'SH' for shirts)

        Returns:
            Unique style code like 'SSG-SH-001'
        """
        assert category_code, "category_code is required"

        cursor = conn.execute(
            """
            SELECT MAX(CAST(SUBSTR(style_code, INSTR(style_code, '-', INSTR(style_code, '-') + 1) + 1) AS INTEGER))
            FROM styles
            WHERE style_code LIKE ?
            """,
            (f"SSG-{category_code}-%",),
        )
        max_num = cursor.fetchone()[0] or 0
        next_num = max_num + 1
        return f"SSG-{category_code}-{next_num:03d}"

    def get_low_stock_variants(
        self,
        conn: sqlite3.Connection,
        threshold: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get variants at or below reorder point.

        Args:
            conn: Database connection
            threshold: Optional override threshold

        Returns:
            List of low stock variant dictionaries
        """
        if threshold is None:
            query = """
                SELECT v.*, s.name as style_name
                FROM variants v
                JOIN styles s ON v.style_id = s.id
                WHERE v.quantity <= v.reorder_point
                ORDER BY v.quantity ASC
            """
            params = []
        else:
            assert threshold >= 0, "threshold must be non-negative"
            query = """
                SELECT v.*, s.name as style_name
                FROM variants v
                JOIN styles s ON v.style_id = s.id
                WHERE v.quantity <= ?
                ORDER BY v.quantity ASC
            """
            params = [threshold]

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_inventory_valuation(
        self,
        conn: sqlite3.Connection,
    ) -> Dict[str, int]:
        """Get total inventory valuation.

        Args:
            conn: Database connection

        Returns:
            Dictionary with cost_value, sale_value, potential_profit (all in cents)
        """
        # Cost value from batches
        cost_cursor = conn.execute(
            """
            SELECT COALESCE(SUM(b.quantity_remaining * b.purchase_price), 0) as cost_value
            FROM batches b
            """
        )
        cost_value = cost_cursor.fetchone()["cost_value"]

        # Sale value from variants
        sale_cursor = conn.execute(
            """
            SELECT COALESCE(SUM(v.quantity * s.base_sale_price), 0) as sale_value
            FROM variants v
            JOIN styles s ON v.style_id = s.id
            """
        )
        sale_value = sale_cursor.fetchone()["sale_value"]

        return {
            "cost_value": cost_value,
            "sale_value": sale_value,
            "potential_profit": sale_value - cost_value,
        }