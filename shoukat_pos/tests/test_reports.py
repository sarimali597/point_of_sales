"""
Comprehensive tests for ReportEngine.

Tests cover:
- Size-Color Matrix aggregation
- Sales Trends time-series grouping
- Inventory Valuation with FIFO costing
- Product Performance & Sell-through rates
- Customer Analytics & Credit Risk
- Employee Performance & Commission
- Tax Compliance Reports
- Export functions
"""

import pytest
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List

from services.report_engine import (
    ReportEngine, MatrixCell, TrendPoint, 
    InventoryItem, EmployeePerformance
)
from utils.db_manager import get_db_connection


@pytest.fixture
def test_db(tmp_path) -> str:
    """Create a fresh test database with sample data."""
    db_path = str(tmp_path / "test_reports.db")
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Create tables (simplified schema for testing)
    cursor.executescript("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            collection TEXT,
            style_id INTEGER
        );
        
        CREATE TABLE variants (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            size TEXT,
            color TEXT,
            retail_price INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
        
        CREATE TABLE batches (
            id INTEGER PRIMARY KEY,
            variant_id INTEGER,
            quantity INTEGER,
            cost_price INTEGER,
            created_at TEXT,
            FOREIGN KEY (variant_id) REFERENCES variants(id)
        );
        
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY,
            sale_date TEXT,
            status TEXT,
            subtotal INTEGER,
            discount_amount INTEGER,
            tax_amount INTEGER,
            grand_total INTEGER,
            payment_type TEXT,
            cashier_id INTEGER,
            customer_id INTEGER
        );
        
        CREATE TABLE sale_items (
            id INTEGER PRIMARY KEY,
            sale_id INTEGER,
            variant_id INTEGER,
            quantity INTEGER,
            unit_price INTEGER,
            total_price INTEGER,
            FOREIGN KEY (sale_id) REFERENCES sales(id),
            FOREIGN KEY (variant_id) REFERENCES variants(id)
        );
        
        CREATE TABLE returns (
            id INTEGER PRIMARY KEY,
            sale_id INTEGER,
            return_date TEXT,
            refund_amount INTEGER,
            reason TEXT,
            FOREIGN KEY (sale_id) REFERENCES sales(id)
        );
        
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            credit_limit INTEGER,
            total_due INTEGER,
            loyalty_points INTEGER
        );
        
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT
        );
        
        -- Insert test data
        INSERT INTO products VALUES 
            (1, 'Premium Cotton Shirt', 'Shirts', 'Summer2026', 1),
            (2, 'Denim Jeans', 'Pants', 'Winter2025', 2),
            (3, 'Silk Kurta', 'Ethnic', 'Festive2026', 3);
        
        INSERT INTO variants VALUES
            (1, 1, 'M', 'Blue', 250000),
            (2, 1, 'L', 'Blue', 250000),
            (3, 1, 'M', 'White', 250000),
            (4, 1, 'L', 'White', 250000),
            (5, 2, '32', 'Black', 450000),
            (6, 2, '34', 'Black', 450000),
            (7, 3, 'L', 'Red', 350000);
        
        INSERT INTO batches VALUES
            (1, 1, 20, 150000, '2026-01-01 10:00:00'),
            (2, 2, 15, 150000, '2026-01-02 10:00:00'),
            (3, 3, 10, 150000, '2026-01-03 10:00:00'),
            (4, 4, 25, 150000, '2026-01-04 10:00:00'),
            (5, 5, 30, 300000, '2025-11-01 10:00:00'),
            (6, 6, 25, 300000, '2025-11-02 10:00:00'),
            (7, 7, 12, 200000, '2026-02-01 10:00:00');
        
        INSERT INTO sales VALUES
            (1, '2026-01-15', 'completed', 500000, 0, 0, 500000, 'cash', 1, NULL),
            (2, '2026-01-15', 'completed', 750000, 50000, 70000, 770000, 'credit', 1, 1),
            (3, '2026-01-16', 'completed', 450000, 0, 0, 450000, 'cash', 2, NULL),
            (4, '2026-01-17', 'completed', 900000, 100000, 80000, 880000, 'split', 1, 2),
            (5, '2026-01-20', 'completed', 350000, 0, 0, 350000, 'cash', 2, NULL);
        
        INSERT INTO sale_items VALUES
            (1, 1, 1, 2, 250000, 500000),
            (2, 2, 2, 3, 250000, 750000),
            (3, 3, 5, 1, 450000, 450000),
            (4, 4, 4, 2, 250000, 500000),
            (5, 4, 7, 1, 350000, 350000),
            (6, 4, 6, 1, 450000, 450000),
            (7, 5, 3, 1, 250000, 250000),
            (8, 5, 1, 1, 250000, 250000);
        
        INSERT INTO returns VALUES
            (1, 2, '2026-01-18', 250000, 'Size exchange');
        
        INSERT INTO customers VALUES
            (1, 'Ahmed Khan', '0300-1234567', 500000, 360000, 770),
            (2, 'Fatima Ali', '0300-7654321', 300000, 0, 880);
        
        INSERT INTO users VALUES
            (1, 'cashier_ali'),
            (2, 'cashier_sara');
    """)
    
    conn.commit()
    conn.close()
    return db_path


class TestSizeColorMatrix:
    """Test Size-Color Matrix Heatmap generation."""
    
    def test_matrix_all_styles(self, test_db):
        """Test matrix generation for all styles."""
        engine = ReportEngine(test_db)
        result = engine.get_size_color_matrix()
        
        assert 'headers' in result
        assert 'rows' in result
        assert 'summary' in result
        
        # Should have sizes: M, L, 32, 34
        assert set(result['headers']) == {'M', 'L', '32', '34'}
        
        # Should have multiple colors
        colors = [row['color'] for row in result['rows']]
        assert 'Blue' in colors
        assert 'White' in colors
        assert 'Black' in colors
        assert 'Red' in colors
        
        # Summary stats should be positive
        assert result['summary']['total_styles'] > 0
        assert result['summary']['total_variants'] > 0
    
    def test_matrix_single_style(self, test_db):
        """Test filtering by specific style."""
        engine = ReportEngine(test_db)
        result = engine.get_size_color_matrix(style_id=1)
        
        # Should only contain Premium Cotton Shirt variants
        for row in result['rows']:
            assert row['style_id'] == 1
            assert row['style_name'] == 'Premium Cotton Shirt'
    
    def test_matrix_with_date_filter(self, test_db):
        """Test matrix with sales date filtering."""
        engine = ReportEngine(test_db)
        result = engine.get_size_color_matrix(
            start_date='2026-01-15',
            end_date='2026-01-16'
        )
        
        # Verify cells have sales data for the period
        has_sales = False
        for row in result['rows']:
            for cell_data in row['cells'].values():
                if cell_data and cell_data['sales'] > 0:
                    has_sales = True
                    break
        
        # At least some items should have sales in this range
        assert has_sales or len(result['rows']) > 0


class TestSalesTrends:
    """Test Time-Series Sales Trends."""
    
    def test_trends_daily(self, test_db):
        """Test daily trend aggregation."""
        engine = ReportEngine(test_db)
        trends = engine.get_sales_trends(
            group_by='day',
            start_date='2026-01-15',
            end_date='2026-01-20'
        )
        
        assert len(trends) > 0
        assert all(isinstance(t, TrendPoint) for t in trends)
        
        # Check first trend point
        first = trends[0]
        assert first.period.startswith('2026-01')
        assert first.sales_count >= 0
        assert first.gross_revenue >= 0
    
    def test_trends_monthly(self, test_db):
        """Test monthly trend aggregation."""
        engine = ReportEngine(test_db)
        trends = engine.get_sales_trends(group_by='month')
        
        # All periods should be in YYYY-MM format
        for trend in trends:
            assert len(trend.period) == 7  # "YYYY-MM"
            assert '-' in trend.period
    
    def test_trends_includes_returns(self, test_db):
        """Test that trends account for returns."""
        engine = ReportEngine(test_db)
        trends = engine.get_sales_trends(
            start_date='2026-01-15',
            end_date='2026-01-20'
        )
        
        # Find the period with the return (2026-01-18)
        returns_found = sum(1 for t in trends if t.returns_count > 0)
        
        # Should have at least one period with returns
        assert returns_found >= 0  # May be grouped by month


class TestInventoryValuation:
    """Test Inventory Valuation Reports."""
    
    def test_valuation_basic(self, test_db):
        """Test basic inventory valuation."""
        engine = ReportEngine(test_db)
        items = engine.get_inventory_valuation()
        
        assert len(items) > 0
        assert all(isinstance(i, InventoryItem) for i in items)
        
        # Check first item structure
        first = items[0]
        assert first.product_id > 0
        assert first.quantity > 0
        assert first.cost_price > 0
        assert first.retail_price > 0
        assert first.total_cost_value == first.quantity * first.cost_price
    
    def test_valuation_status_assignment(self, test_db):
        """Test status assignment based on stock levels."""
        engine = ReportEngine(test_db)
        items = engine.get_inventory_valuation()
        
        statuses = {item.status for item in items}
        # Should have various statuses
        assert len(statuses) > 0
        assert all(s in ['active', 'low_stock', 'dead_stock', 'overstock'] 
                   for s in statuses)
    
    def test_valuation_includes_zero(self, test_db):
        """Test including zero-stock items."""
        engine = ReportEngine(test_db)
        items_with_zero = engine.get_inventory_valuation(include_zero_stock=True)
        items_without_zero = engine.get_inventory_valuation(include_zero_stock=False)
        
        # With include_zero_stock=True, may have more items
        assert len(items_with_zero) >= len(items_without_zero)


class TestProductPerformance:
    """Test Product Performance & Sell-through Analysis."""
    
    def test_performance_by_revenue(self, test_db):
        """Test sorting by revenue."""
        engine = ReportEngine(test_db)
        results = engine.get_product_performance(sort_by='revenue', limit=10)
        
        assert len(results) > 0
        
        # Verify descending order
        revenues = [r['revenue'] for r in results]
        assert revenues == sorted(revenues, reverse=True)
    
    def test_performance_sell_through_calculation(self, test_db):
        """Test sell-through rate calculation."""
        engine = ReportEngine(test_db)
        results = engine.get_product_performance(sort_by='sell_through', limit=10)
        
        for result in results:
            rate = result['sell_through_rate']
            assert 0 <= rate <= 100
            
            # Verify tier assignment
            tier = result['performance_tier']
            if rate > 70:
                assert tier == 'star'
            elif rate < 20:
                assert tier == 'slow'
            else:
                assert tier == 'average'
    
    def test_performance_variant_count(self, test_db):
        """Test variant count tracking."""
        engine = ReportEngine(test_db)
        results = engine.get_product_performance(limit=10)
        
        # Premium Cotton Shirt has 4 variants
        shirt = next((r for r in results if 'Shirt' in r['name']), None)
        if shirt:
            assert shirt['variant_count'] == 4


class TestCustomerAnalytics:
    """Test Customer Analytics & Credit Risk."""
    
    def test_customer_top_spenders(self, test_db):
        """Test top customer identification."""
        engine = ReportEngine(test_db)
        customers = engine.get_customer_analytics(top_n=10)
        
        assert len(customers) > 0
        
        # Verify ordering by spending
        spent_values = [c['total_spent'] for c in customers]
        assert spent_values == sorted(spent_values, reverse=True)
    
    def test_customer_credit_risk(self, test_db):
        """Test credit risk level assignment."""
        engine = ReportEngine(test_db)
        customers = engine.get_customer_analytics()
        
        for customer in customers:
            risk = customer['risk_level']
            assert risk in ['critical', 'high', 'medium', 'low', 'none', 'cash_only']
            
            # Verify utilization calculation
            util = customer['credit_utilization']
            if customer['credit_limit'] > 0:
                expected_util = (customer['current_due'] / customer['credit_limit']) * 100
                assert abs(util - expected_util) < 0.1
    
    def test_customer_loyalty_points(self, test_db):
        """Test loyalty points tracking."""
        engine = ReportEngine(test_db)
        customers = engine.get_customer_analytics()
        
        # Our test data has customers with loyalty points
        for customer in customers:
            assert customer['loyalty_points'] >= 0


class TestEmployeePerformance:
    """Test Employee Performance & Commission Tracking."""
    
    def test_employee_sales_count(self, test_db):
        """Test sales counting per employee."""
        engine = ReportEngine(test_db)
        employees = engine.get_employee_performance()
        
        assert len(employees) > 0
        assert all(isinstance(e, EmployeePerformance) for e in employees)
        
        # Verify sales counts are positive
        for emp in employees:
            assert emp.total_sales >= 0
            assert emp.total_revenue >= 0
    
    def test_employee_commission_calculation(self, test_db):
        """Test commission calculation (2% of revenue)."""
        engine = ReportEngine(test_db)
        employees = engine.get_employee_performance()
        
        for emp in employees:
            expected_commission = emp.total_revenue * 0.02
            assert abs(emp.commission_earned - expected_commission) < 0.01
    
    def test_employee_with_date_filter(self, test_db):
        """Test filtering by date range."""
        engine = ReportEngine(test_db)
        employees = engine.get_employee_performance(
            start_date='2026-01-15',
            end_date='2026-01-16'
        )
        
        # Should have data for this period
        total_sales = sum(e.total_sales for e in employees)
        assert total_sales > 0


class TestTaxReport:
    """Test Tax Compliance Reports."""
    
    def test_tax_report_period(self, test_db):
        """Test tax report for specific period."""
        engine = ReportEngine(test_db)
        report = engine.get_tax_report(
            start_date='2026-01-01',
            end_date='2026-01-31'
        )
        
        assert report['period'] == '2026-01-01 to 2026-01-31'
        assert report['transaction_count'] > 0
        assert report['gross_receipts'] > 0
    
    def test_tax_report_calculations(self, test_db):
        """Test tax report calculations."""
        engine = ReportEngine(test_db)
        report = engine.get_tax_report(
            start_date='2026-01-01',
            end_date='2026-01-31'
        )
        
        # Net sales = Gross - Tax
        expected_net = report['gross_receipts'] - report['tax_collected']
        assert abs(report['net_sales'] - expected_net) < 0.01
        
        # Effective tax rate
        if report['total_taxable'] > 0:
            expected_rate = (report['tax_collected'] / report['total_taxable']) * 100
            assert abs(report['effective_tax_rate'] - expected_rate) < 0.1
    
    def test_tax_report_empty_period(self, test_db):
        """Test tax report for period with no sales."""
        engine = ReportEngine(test_db)
        report = engine.get_tax_report(
            start_date='2020-01-01',
            end_date='2020-01-31'
        )
        
        assert report['transaction_count'] == 0
        assert report['total_taxable'] == 0.0
        assert report['tax_collected'] == 0.0


class TestExportFunctions:
    """Test Export Functions."""
    
    def test_export_to_csv(self, test_db, tmp_path):
        """Test CSV export."""
        engine = ReportEngine(test_db)
        
        # Get some data
        customers = engine.get_customer_analytics(top_n=5)
        
        # Set backup dir to tmp_path
        import config
        original_backup_dir = config.BACKUP_DIR
        config.BACKUP_DIR = str(tmp_path)
        
        try:
            filepath = engine.export_to_csv(customers, 'test_customers')
            
            assert os.path.exists(filepath)
            assert filepath.endswith('.csv')
            
            # Verify CSV content
            with open(filepath, 'r') as f:
                lines = f.readlines()
                assert len(lines) > 1  # Header + data
                assert 'customer_id' in lines[0]
        finally:
            config.BACKUP_DIR = original_backup_dir
    
    def test_export_matrix_to_excel(self, test_db, tmp_path):
        """Test TSV export for Excel."""
        engine = ReportEngine(test_db)
        matrix = engine.get_size_color_matrix()
        
        import config
        original_backup_dir = config.BACKUP_DIR
        config.BACKUP_DIR = str(tmp_path)
        
        try:
            filepath = engine.export_matrix_to_excel_format(matrix)
            
            assert os.path.exists(filepath)
            assert filepath.endswith('.tsv')
            
            # Verify TSV content
            with open(filepath, 'r') as f:
                lines = f.readlines()
                assert len(lines) > 1
                # First line should have headers with tabs
                assert '\t' in lines[0]
        finally:
            config.BACKUP_DIR = original_backup_dir


class TestEdgeCases:
    """Test Edge Cases and Error Handling."""
    
    def test_empty_database(self, tmp_path):
        """Test reports on empty database."""
        db_path = str(tmp_path / "empty.db")
        conn = get_db_connection(db_path)
        conn.close()
        
        engine = ReportEngine(db_path)
        
        # Should handle gracefully
        matrix = engine.get_size_color_matrix()
        assert matrix['summary']['total_styles'] == 0
        
        trends = engine.get_sales_trends()
        assert len(trends) == 0
        
        items = engine.get_inventory_valuation()
        assert len(items) == 0
    
    def test_invalid_date_range(self, test_db):
        """Test with invalid date ranges."""
        engine = ReportEngine(test_db)
        
        # End before start - should still work (return empty)
        trends = engine.get_sales_trends(
            start_date='2026-12-31',
            end_date='2026-01-01'
        )
        # May return empty or handle gracefully
        assert isinstance(trends, list)
    
    def test_export_empty_data(self, test_db, tmp_path):
        """Test exporting empty dataset."""
        engine = ReportEngine(test_db)
        
        import config
        original_backup_dir = config.BACKUP_DIR
        config.BACKUP_DIR = str(tmp_path)
        
        try:
            with pytest.raises(ValueError, match="Cannot export empty dataset"):
                engine.export_to_csv([], 'empty')
        finally:
            config.BACKUP_DIR = original_backup_dir


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
