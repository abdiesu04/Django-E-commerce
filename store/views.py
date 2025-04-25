from django.shortcuts import render
from django.db.models import Sum, F, DecimalField
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.views.decorators.cache import cache_page

from .models import Product, PurchaseOrder, Invoice
from . import queries

# Create your views here.
def home(request):
    """
    Home page view for the e-commerce store
    """
    # Get some basic statistics
    product_count = Product.objects.count()
    purchase_order_count = PurchaseOrder.objects.count()
    invoice_count = Invoice.objects.count()
    
    # Get the total value of all invoices
    total_invoice_value = Invoice.objects.annotate(
        total=Sum(F('line_items__quantity') * F('line_items__price_each'), 
                 output_field=DecimalField())
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Get the total value of all purchase orders
    total_purchase_value = PurchaseOrder.objects.annotate(
        total=Sum(F('line_items__quantity') * F('line_items__cost_per_unit'), 
                 output_field=DecimalField())
    ).aggregate(Sum('total'))['total__sum'] or 0
    
    # Get overdue invoices
    overdue_invoices_count = queries.get_overdue_invoices().count()
    
    # Get low stock products
    low_stock_products_count = queries.get_low_stock_products().count()
    
    context = {
        'title': 'Welcome to Our E-commerce Management System',
        'product_count': product_count,
        'purchase_order_count': purchase_order_count,
        'invoice_count': invoice_count,
        'total_invoice_value': total_invoice_value,
        'total_purchase_value': total_purchase_value,
        'overdue_invoices_count': overdue_invoices_count,
        'low_stock_products_count': low_stock_products_count
    }
    return render(request, 'store/home.html', context)

@staff_member_required
def dashboard(request):
    """
    Admin dashboard with detailed statistics
    """
    # Try to get dashboard data from cache
    cache_key = 'dashboard_data'
    dashboard_data = cache.get(cache_key)
    
    if dashboard_data is None:
        # Only run expensive queries if cache is empty
        # Limit data retrieval to what's necessary
        top_products = list(queries.get_product_sales_analysis()[:5])
        vendor_summary = list(queries.get_vendor_purchase_summary()[:5])
        invoice_summary = list(queries.get_invoice_status_summary())
        top_customers = list(queries.get_customers_by_revenue()[:5])
        product_margins = list(queries.get_product_profit_margin()[:5])
        
        # Store in cache for 5 minutes
        dashboard_data = {
            'top_products': top_products,
            'vendor_summary': vendor_summary,
            'invoice_summary': invoice_summary,
            'top_customers': top_customers,
            'product_margins': product_margins
        }
        cache.set(cache_key, dashboard_data, 300)  # 5 minutes
    
    context = {
        'title': 'Admin Dashboard',
        'top_products': dashboard_data['top_products'],
        'vendor_summary': dashboard_data['vendor_summary'],
        'invoice_summary': dashboard_data['invoice_summary'],
        'top_customers': dashboard_data['top_customers'],
        'product_margins': dashboard_data['product_margins']
    }
    return render(request, 'store/dashboard.html', context)
