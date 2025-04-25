from django.db.models import Sum, F, DecimalField, Count, Q, Avg, Case, When, Value, IntegerField
from django.utils import timezone
from .models import Product, PurchaseOrder, Invoice, InvoiceLineItem, PurchaseOrderLineItem
from django.core.cache import cache

def get_high_value_invoices(min_total_amount=1000):
    """
    Get invoices with a total amount greater than the specified minimum
    Using annotation to calculate the total amount for each invoice
    """
    return Invoice.objects.annotate(
        total_amount=Sum(F('line_items__quantity') * F('line_items__price_each'), 
                        output_field=DecimalField())
    ).filter(total_amount__gt=min_total_amount)

def get_overdue_invoices():
    """
    Get all overdue invoices that are not paid or cancelled
    """
    today = timezone.now().date()
    return Invoice.objects.filter(
        due_date__lt=today,
        status__in=['draft', 'sent', 'overdue']
    )

def get_invoices_by_status_with_totals():
    """
    Group invoices by status and get the count and total amount for each status
    """
    return Invoice.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum(F('line_items__quantity') * F('line_items__price_each'), 
                        output_field=DecimalField())
    ).order_by('status')

def get_product_sales_analysis():
    """
    Get a sales analysis for each product, including total quantity sold and revenue
    """
    return Product.objects.annotate(
        quantity_sold=Sum('invoicelineitem__quantity'),
        total_revenue=Sum(F('invoicelineitem__quantity') * F('invoicelineitem__price_each'), 
                        output_field=DecimalField())
    ).filter(quantity_sold__gt=0).order_by('-total_revenue')

def get_vendor_purchase_summary():
    """
    Get a summary of purchases by vendor, including total orders and amount spent
    """
    return PurchaseOrder.objects.values('vendor_name').annotate(
        order_count=Count('id'),
        total_spent=Sum(F('line_items__quantity') * F('line_items__cost_per_unit'), 
                        output_field=DecimalField())
    ).order_by('-total_spent')

def get_product_profit_margin():
    """
    Calculate the profit margin for each product
    Using complex annotation to compare sales price vs. purchase cost
    """
    return Product.objects.annotate(
        avg_purchase_price=Avg('purchaseorderlineitem__cost_per_unit'),
        avg_sales_price=Avg('invoicelineitem__price_each'),
        profit_margin=Case(
            When(avg_purchase_price__gt=0, 
                 then=100 * (F('avg_sales_price') - F('avg_purchase_price')) / F('avg_purchase_price')),
            default=Value(0),
            output_field=DecimalField()
        )
    ).filter(avg_purchase_price__gt=0, avg_sales_price__gt=0).order_by('-profit_margin')

def get_monthly_sales_report(year=None):
    """
    Get a monthly sales report for a specific year
    Group by month and calculate total sales
    """
    if not year:
        year = timezone.now().year
        
    return Invoice.objects.filter(
        invoice_date__year=year,
        status__in=['sent', 'paid']
    ).annotate(
        month=F('invoice_date__month')
    ).values('month').annotate(
        invoice_count=Count('id'),
        total_sales=Sum(F('line_items__quantity') * F('line_items__price_each'), 
                       output_field=DecimalField())
    ).order_by('month')

def get_low_stock_products(threshold=10):
    """
    Get products with stock below the specified threshold
    """
    return Product.objects.filter(stock_quantity__lt=threshold).order_by('stock_quantity')

def get_customers_by_revenue():
    """
    Get customers ranked by total revenue
    """
    return Invoice.objects.values('customer_name', 'customer_email').annotate(
        invoice_count=Count('id'),
        total_spent=Sum(F('line_items__quantity') * F('line_items__price_each'), 
                       output_field=DecimalField())
    ).order_by('-total_spent')

def get_products_never_purchased():
    """
    Get products that have never been purchased (not in any invoice)
    Using a subquery to find products not in invoice line items
    """
    return Product.objects.exclude(
        id__in=InvoiceLineItem.objects.values_list('product_id', flat=True)
    )

def get_invoice_status_summary():
    """
    Get a summary of invoices by status with additional flags for overdue
    Using conditional expressions with Case/When with optimization
    """
    # Use cache key based on the last modified invoice to avoid recalculating unnecessarily
    cache_key = 'invoice_status_summary'
    cached_result = cache.get(cache_key)
    
    # If cached result exists and isn't too old, return it
    if cached_result is not None:
        return cached_result
    
    today = timezone.now().date()
    
    # More efficient query that doesn't compute complex aggregations for every row
    result = Invoice.objects.annotate(
        is_overdue=Case(
            When(due_date__lt=today, status__in=['draft', 'sent'], then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )
    ).values('status').annotate(
        count=Count('id'),
        overdue_count=Sum('is_overdue')
    ).order_by('status')
    
    # Calculate totals in separate, simpler query
    status_totals = {}
    for status in result:
        invoices = Invoice.objects.filter(status=status['status'])
        total = 0
        for invoice in invoices:
            total += invoice.get_total_amount()
        status['status_total'] = total
    
    # Cache the result for 10 minutes
    cache.set(cache_key, result, 600)
    
    return result 