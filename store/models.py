from django.db import models
from django.db.models import Sum, F, DecimalField
from django.utils import timezone
import uuid

class Product(models.Model):
    """Model for storing product information"""
    name = models.CharField(max_length=255, db_index=True)
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit", db_index=True)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0, db_index=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def get_inventory_value(self):
        """Calculate the total inventory value for this product"""
        if self.unit_price is None:
            return 0
        return self.unit_price * self.stock_quantity

class PurchaseOrder(models.Model):
    """Model for purchase orders from vendors"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    )
    
    order_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    vendor_name = models.CharField(max_length=255)
    order_date = models.DateTimeField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'

    def __str__(self):
        return f"PO #{self.order_number} - {self.vendor_name}"

    def get_total_cost(self):
        """Calculate the total cost of the purchase order"""
        return self.line_items.aggregate(
            total=Sum(F('quantity') * F('cost_per_unit'), output_field=DecimalField())
        )['total'] or 0
    
    def get_total_items(self):
        """Get total number of items ordered"""
        return self.line_items.aggregate(Sum('quantity'))['quantity__sum'] or 0

class PurchaseOrderLineItem(models.Model):
    """Model for individual line items on purchase orders"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='line_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = 'Purchase Order Line Item'
        verbose_name_plural = 'Purchase Order Line Items'
        unique_together = ['purchase_order', 'product']

    def __str__(self):
        return f"{self.quantity} x {self.product.name} @ ${self.cost_per_unit}"
    
    def get_subtotal(self):
        """Calculate the subtotal for this line item"""
        return self.quantity * self.cost_per_unit

class Invoice(models.Model):
    """Model for customer invoices"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4, db_index=True)
    customer_name = models.CharField(max_length=255, db_index=True)
    customer_email = models.EmailField(db_index=True)
    billing_address = models.TextField()
    invoice_date = models.DateTimeField(default=timezone.now, db_index=True)
    due_date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-invoice_date']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.customer_name}"

    def get_total_amount(self):
        """Calculate the total amount of the invoice"""
        return self.line_items.aggregate(
            total=Sum(F('quantity') * F('price_each'), output_field=DecimalField())
        )['total'] or 0
    
    def is_overdue(self):
        """Check if the invoice is overdue"""
        if self.status == 'paid' or self.status == 'cancelled':
            return False
        return self.due_date < timezone.now().date()
    
    def mark_as_paid(self):
        """Mark the invoice as paid"""
        self.status = 'paid'
        self.save()

class InvoiceLineItem(models.Model):
    """Model for individual line items on invoices"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_each = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Invoice Line Item'
        verbose_name_plural = 'Invoice Line Items'
        unique_together = ['invoice', 'product']

    def __str__(self):
        return f"{self.quantity} x {self.product.name} @ ${self.price_each}"
    
    def get_subtotal(self):
        """Calculate the subtotal for this line item"""
        return self.quantity * self.price_each
