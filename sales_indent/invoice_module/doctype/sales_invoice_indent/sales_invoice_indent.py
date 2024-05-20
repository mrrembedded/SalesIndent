import frappe
import re
from datetime import datetime
from frappe.model.document import Document

class SalesInvoiceIndent(Document):
    # Validity Check for Quantity 
    def after_insert(self):
        try:
            doc_name = self.name
            frappe.msgprint(doc_name)
            
            sql_name = """
                SELECT product__code, rate, billed_qty, billed_amount, qty
                FROM `tabProduction`
                WHERE parent = %s;
            """                                                 

            name_docs = frappe.db.sql(sql_name, (doc_name,))
            
            if not name_docs:
                raise ValueError("No product items found")

            for child_doc in name_docs:
                item_code = child_doc[0]
                item_price = float(child_doc[1])  # Convert currency to float
                quantity = float(child_doc[2])
                billed_amount = float(child_doc[3])
                sales_qty = float(child_doc[4])

                # Calculate quantity billed
                quantity_billed = billed_amount / item_price

                # Calculate remaining quantity
                remaining_quantity = sales_qty - quantity_billed

                if quantity > remaining_quantity:
                    frappe.msgprint("Quantity Exceeds")
                    frappe.msgprint(f"Item code: {item_code}, Qty to Bill: {quantity}, Remaining Qty: {remaining_quantity}")
                else:
                    frappe.msgprint("Deliver to bill")
                    frappe.msgprint(f"Item code: {item_code}, Qty to Bill: {quantity}")
        except Exception as e:
            frappe.log_error(f"Error in after_insert(): {str(e)}")
            raise

    # Sales Invoice Creation
    def before_submit(self):
        try:
            doc_name = self.name
            doc_vehicle_no = self.vehicle_no

            if not re.match(r"[A-Z]{2}[0-9]{1,2}[A-Z]{1,2}[0-9]{4}", doc_vehicle_no):
                frappe.throw("Enter a valid vehicle number Without Space")
                return
            else:
                frappe.msgprint("You have entered valid vehicle number")

            sql_name = """
                SELECT product__code, rate, billed_qty, billed_amount, qty
                FROM `tabProduction`
                WHERE parent = %s;
            """                                                 

            name_docs = frappe.db.sql(sql_name, (doc_name,))
            
            if not name_docs:
                raise ValueError("No product items found")

            for child_doc in name_docs:
                item_code = child_doc[0]
                item_price = float(child_doc[1])  # Convert currency to float
                quantity = float(child_doc[2])
                billed_amount = float(child_doc[3])
                sales_qty = float(child_doc[4])

                # Calculate quantity billed
                quantity_billed = billed_amount / item_price

                # Calculate remaining quantity
                remaining_quantity = sales_qty - quantity_billed
                try:
                    if quantity > remaining_quantity:
                        frappe.throw(f"Quantity for item {item_code} exceeds available quantity")
                    else:
                        frappe.msgprint("Success to Deliver to bill")
                        
                except Exception as e:
                    frappe.throw(f"Cannot submit document because {item_code} quantity exceeds available quantity")
                    raise
               
            doc_name_two = self.name
            doc_date = self.date

            sql_query = """
                SELECT product__code, customer, po_date, po_no, billed_qty, rate,
                       taxes_and_charges, payment_term_template, payment_term, supplier_code,
                       sales_order
                FROM `tabProduction`
                WHERE parent = %s;
            """                                                 

            child_docs = frappe.db.sql(sql_query, (doc_name_two,))
                    
            if not child_docs:
                raise ValueError("No product items found")

            for child_doc in child_docs:
                # Extract values from the fetched data for each record
                product_code_value = child_doc[0]
                customer_value = child_doc[1]
                po_date_value = child_doc[2]
                po_no_value = child_doc[3]
                billed_qty_value = float(child_doc[4])
                rate_value = float(child_doc[5])
                taxes_charges_value = child_doc[6]
                payment_term_temp_value = child_doc[7]
                payment_term_value = child_doc[8]
                supplierCode_value = child_doc[9]
                salesOrder_value = child_doc[10]

                # Parse po_date_value to datetime object
                if isinstance(po_date_value, str):
                    po_date_value = datetime.strptime(po_date_value, "%Y-%m-%d")

                sql_tax = """
                    SELECT rate, account_head, charge_type, description 
                    FROM `tabSales Taxes and Charges` 
                    WHERE parent= %s;
                """

                tax_docs = frappe.db.sql(sql_tax, (salesOrder_value,))

                # Create a list to store tax details
                taxes_list = []

                for tax_doc in tax_docs:
                    rateValue = tax_doc[0]
                    accountHead_value = tax_doc[1]
                    chargeType = tax_doc[2]
                    description = tax_doc[3]

                    # Create a dictionary for each tax and append it to the taxes list
                    tax_detail = {
                        "charge_type": chargeType,
                        "account_head": accountHead_value,
                        "rate": rateValue,
                        "description": description
                    }
                    taxes_list.append(tax_detail)

                # Create sales invoice data for each record
                sales_invoice_data = {
                    "doctype": "Sales Invoice",
                    "customer": customer_value,
                    "posting_date": doc_date,
                    "indent_no": doc_name_two,
                    "supplier_code": supplierCode_value,
                    "po_no": po_no_value,
                    "po_date": po_date_value.strftime("%Y-%m-%d"),  # Convert date to string in required format
                    "items": [
                        {
                            "item_code": product_code_value,
                            "qty": billed_qty_value,
                            "rate": rate_value,
                        }
                    ],
                    "taxes_and_charges": taxes_charges_value,
                    "payment_term_template": payment_term_temp_value,
                    "vehicle_no": doc_vehicle_no,
                    "taxes": taxes_list  # Assign the taxes list to the taxes key
                }

                # Create a new Sales Invoice document
                sales_invoice = frappe.get_doc(sales_invoice_data)
                sales_invoice.insert()

                # Save the Sales Invoice
                sales_invoice.save()
                frappe.msgprint("Sales Invoice created successfully.")        

            try:
                # Fetch counts
                product_count = frappe.get_value("Product Item", {"parent": self.name}, "count(name)")
                sales_count = frappe.get_value("Sales Invoice", {"indent_no": self.name}, "count(name)")

                if product_count == sales_count:
                    frappe.msgprint("Product count and invoice count are equal")
                else:
                    frappe.throw("Product count and invoice count are not equal")

            except Exception as e:
                frappe.msgprint(f"Error: {str(e)}") 

        except Exception as e:
            frappe.log_error(f"Error in before_submit(): {str(e)}")
            raise

import traceback

def insertSelect_item():
    try:
        sql_truncate = "TRUNCATE TABLE `tabIndent Item`;"
        frappe.db.sql(sql_truncate)

        sql_insert = """
        INSERT INTO `tabIndent Item` (`name`, `sales_order`, `rate`, `billed_amount`, `qty`)
        SELECT item_code, parent, rate, billed_amt, qty
        FROM `tabSales Order Item`
        WHERE parent IN (
            SELECT name
            FROM `tabSales Order`
            WHERE status = "To Deliver and Bill"
            AND (billing_status = "Partly Billed" OR billing_status = "Not Billed") AND delivery_date >= CURDATE()
        );
        """
        # Execute the SQL query
        frappe.db.sql(sql_insert)

        sql_update = """
        UPDATE `tabIndent Item` AS ic
        JOIN (
            SELECT
            ic.name,
            MAX(so.po_no) AS max_po_no,
            MAX(so.po_date) AS max_po_date,
            MAX(so.customer) AS max_customer,
            MAX(so.supplier_code) AS max_supplier_code,
            MAX(so.company) AS max_company,
            MAX(so.taxes_and_charges) AS max_taxes_and_charges,
            MAX(so.payment_terms_template) AS max_payment_terms_template,
            MAX(so.tc_name) AS max_tc_name
            FROM `tabItemCodeIndent` AS ic
            JOIN `tabSales Order` AS so ON so.name = ic.sales_order
            GROUP BY ic.name
        ) AS mv ON mv.name = ic.name
        SET
            ic.po_no = mv.max_po_no,
            ic.po_date = mv.max_po_date,
            ic.customer = mv.max_customer,
            ic.supplier_code = mv.max_supplier_code,
            ic.company = mv.max_company,
            ic.sales_taxes_and_charges_template = mv.max_taxes_and_charges,
            ic.payment_terms_template = mv.max_payment_terms_template,
            ic.payment_term = mv.max_tc_name;
        """

        # Execute the SQL query
        frappe.db.sql(sql_update)

        # Commit the changes
        frappe.db.commit()

        frappe.msgprint("Sales Order Updated successfully")

    except Exception as e:
        # Print the full traceback of the exception
        traceback.print_exc()
        frappe.msgprint(f"Error: {str(e)}")  # Display error message

insertSelect_item()
