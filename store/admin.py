from django.contrib import admin
from django.db.models import Sum, F, DecimalField
from django.http import HttpResponse
from django.utils.html import format_html
from django.contrib import messages

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.drawing.image import Image
from io import BytesIO

from .models import (
    Product, 
    PurchaseOrder, 
    PurchaseOrderLineItem, 
    Invoice, 
    InvoiceLineItem
)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'unit_price', 'stock_quantity', 'inventory_value')
    list_filter = ('created_at',)
    search_fields = ('name', 'sku', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'description', 'image')
        }),
        ('Pricing and Inventory', {
            'fields': ('unit_price', 'stock_quantity')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def inventory_value(self, obj):
        return f"${obj.get_inventory_value()}"
    inventory_value.short_description = 'Inventory Value'

class PurchaseOrderLineItemInline(admin.TabularInline):
    model = PurchaseOrderLineItem
    min_num = 1
    extra = 0
    fields = ('product', 'quantity', 'cost_per_unit', 'received_quantity', 'subtotal')
    readonly_fields = ('subtotal',)
    
    def subtotal(self, obj):
        if obj.id:
            return f"${obj.get_subtotal()}"
        return "$0.00"
    subtotal.short_description = 'Subtotal'

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'vendor_name', 'order_date', 'status', 'total_cost', 'total_items')
    list_filter = ('status', 'order_date')
    search_fields = ('order_number', 'vendor_name', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'total_cost_display')
    inlines = [PurchaseOrderLineItemInline]
    date_hierarchy = 'order_date'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'vendor_name', 'status')
        }),
        ('Dates', {
            'fields': ('order_date', 'expected_delivery_date')
        }),
        ('Additional Information', {
            'fields': ('notes', 'total_cost_display')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_cost(self, obj):
        return f"${obj.get_total_cost()}"
    total_cost.short_description = 'Total Cost'
    
    def total_items(self, obj):
        return obj.get_total_items()
    total_items.short_description = 'Total Items'
    
    def total_cost_display(self, obj):
        return format_html('<div style="font-size: 1.2em; color: #28a745; font-weight: bold;">${}</div>', obj.get_total_cost())
    total_cost_display.short_description = 'Total Cost'

class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    min_num = 1
    extra = 0
    fields = ('product', 'quantity', 'price_each', 'subtotal')
    readonly_fields = ('subtotal',)
    
    def subtotal(self, obj):
        if obj.id:
            return f"${obj.get_subtotal()}"
        return "$0.00"
    subtotal.short_description = 'Subtotal'

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer_name', 'invoice_date', 'due_date', 'status_colored', 'total_amount')
    list_filter = ('status', 'invoice_date', 'due_date')
    search_fields = ('invoice_number', 'customer_name', 'customer_email', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'total_amount_display')
    inlines = [InvoiceLineItemInline]
    date_hierarchy = 'invoice_date'
    actions = ['mark_as_paid', 'export_to_xlsx']
    
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'customer_name', 'customer_email')
        }),
        ('Billing Details', {
            'fields': ('billing_address',)
        }),
        ('Dates and Status', {
            'fields': ('invoice_date', 'due_date', 'status')
        }),
        ('Additional Information', {
            'fields': ('notes', 'total_amount_display')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_amount(self, obj):
        return f"${obj.get_total_amount()}"
    total_amount.short_description = 'Total Amount'
    
    def status_colored(self, obj):
        colors = {
            'draft': '#6c757d',      # Gray
            'sent': '#17a2b8',       # Info blue
            'paid': '#28a745',       # Success green
            'cancelled': '#dc3545',  # Danger red
            'overdue': '#dc3545'     # Danger red
        }
        
        if obj.is_overdue() and obj.status != 'paid' and obj.status != 'cancelled':
            return format_html('<span style="color: {}; font-weight: bold;">OVERDUE</span>', colors['overdue'])
        
        return format_html('<span style="color: {};">{}</span>', 
                          colors.get(obj.status, '#6c757d'), 
                          obj.get_status_display())
    status_colored.short_description = 'Status'
    
    def total_amount_display(self, obj):
        return format_html('<div style="font-size: 1.2em; color: #28a745; font-weight: bold;">${}</div>', obj.get_total_amount())
    total_amount_display.short_description = 'Total Amount'
    
    def mark_as_paid(self, request, queryset):
        updated = 0
        for invoice in queryset:
            if invoice.status != 'paid':
                invoice.status = 'paid'
                invoice.save()
                updated += 1
        
        if updated == 0:
            messages.warning(request, 'No invoices were marked as paid.')
        else:
            messages.success(request, f'{updated} {"invoice was" if updated == 1 else "invoices were"} successfully marked as paid.')
    mark_as_paid.short_description = 'Mark selected invoices as paid'
    
    def export_to_xlsx(self, request, queryset):
        """Export invoice details to XLSX file"""
        if queryset.count() != 1:
            messages.warning(request, 'Please select only one invoice to export.')
            return
        
        invoice = queryset.first()
        
        # Create workbook and sheet
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Invoice {invoice.invoice_number}"
        
        # Define styles
        header_font = Font(bold=True, size=12)
        header_fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
        
        # Company header
        ws.merge_cells('A1:F1')
        ws['A1'] = 'E-COMMERCE MANAGEMENT SYSTEM'
        ws['A1'].font = Font(bold=True, size=16)
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Invoice information
        ws['A3'] = 'Invoice Number:'
        ws['B3'] = str(invoice.invoice_number)
        ws['A3'].font = header_font
        
        ws['A4'] = 'Date:'
        ws['B4'] = invoice.invoice_date.strftime('%Y-%m-%d')
        ws['A4'].font = header_font
        
        ws['A5'] = 'Due Date:'
        ws['B5'] = invoice.due_date.strftime('%Y-%m-%d')
        ws['A5'].font = header_font
        
        ws['A6'] = 'Status:'
        ws['B6'] = invoice.get_status_display()
        ws['A6'].font = header_font
        
        # Customer information
        ws['D3'] = 'Customer:'
        ws['E3'] = invoice.customer_name
        ws['D3'].font = header_font
        
        ws['D4'] = 'Email:'
        ws['E4'] = invoice.customer_email
        ws['D4'].font = header_font
        
        ws['D5'] = 'Billing Address:'
        ws['E5'] = invoice.billing_address.replace("\n", ", ")
        ws['D5'].font = header_font
        
        # Line items header
        row = 8
        headers = ['Product', 'SKU', 'Quantity', 'Price Each', 'Subtotal']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        # Line items
        row += 1
        for item in invoice.line_items.all():
            ws.cell(row=row, column=1, value=item.product.name)
            ws.cell(row=row, column=2, value=item.product.sku)
            ws.cell(row=row, column=3, value=item.quantity)
            ws.cell(row=row, column=4, value=float(item.price_each))
            ws.cell(row=row, column=5, value=float(item.get_subtotal()))
            row += 1
        
        # Total
        ws.cell(row=row+1, column=4, value='Total:')
        ws.cell(row=row+1, column=4).font = header_font
        ws.cell(row=row+1, column=5, value=float(invoice.get_total_amount()))
        ws.cell(row=row+1, column=5).font = header_font
        
        # Adjust column widths
        for col in ['A', 'B', 'C', 'D', 'E']:
            ws.column_dimensions[col].width = 20
        
        # Create response
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=Invoice_{invoice.invoice_number}.xlsx'
        return response
    export_to_xlsx.short_description = 'Export to XLSX'
    
# We don't register these models directly as they are used in inlines
# admin.site.register(PurchaseOrderLineItem)
# admin.site.register(InvoiceLineItem)
