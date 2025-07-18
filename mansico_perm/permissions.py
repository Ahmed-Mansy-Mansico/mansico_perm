
import frappe

class GenFilters:
    def __init__(self, doctype, *args, **kwargs):
        self.doctype = doctype
        self.args = args
        self.kwargs = kwargs
        self._customer_names = None
        self._doctype_fields_map = None
        self._custom_permission = None
        self.perm_doctype = frappe.db.get_single_value("Custom Permissions", "doctype_name")
        self.user_field = frappe.db.get_single_value("Custom Permissions", "user_field")
        self.role_perm = frappe.db.get_single_value("Custom Permissions", "role")
        self._custom_permission = (frappe.db.get_single_value("Custom Permissions", "disabled") == 0)

    @property
    def custom_permission(self):
        """Check if user has Custom Permissions"""
        return self._custom_permission and self.role_perm in frappe.get_roles(frappe.session.user)

    @property
    def customer_names(self):
        """Get customer names managed by current user"""
        if self._customer_names is None:
            self._customer_names = frappe.get_all(
                self.perm_doctype,
                filters={self.user_field: frappe.session.user},
                pluck="name"
            ) or []
        return self._customer_names

    @property
    def doctypes_to_filter(self):
        """Get mapping of doctypes to their customer link fields"""
        if self._doctype_fields_map is None:
            fields = frappe.get_all(
                "DocField",
                filters={
                    "fieldtype": "Link",
                    "options": self.perm_doctype,
                },
                fields=["parent", "fieldname"],
                distinct=True
            )
            self._doctype_fields_map = {
                field["parent"]: field["fieldname"]
                for field in fields 
                if field["parent"] != self.perm_doctype
            }
        return self._doctype_fields_map

    @property
    def field_name(self):
        field = frappe.db.get_value(
                "DocField",
                {
                    "fieldtype": "Link",
                    "options": self.perm_doctype,
                    "parent": self.doctype,
                },
                ["fieldname"]
            )
        return field or None


    def get_instances_has_customer(self):
        """Generate filters for doctypes with customer links"""
        if not self.customer_names:
            return None
            
        customer_field = self.doctypes_to_filter.get(self.doctype)
        if not customer_field:
            return None
        return [self.doctype, customer_field, 'in', self.customer_names]

    def refactor_data(self, data):
        # data is Report Data General Ledger
        if not self.customer_names:
            return data
        response = []
        for row in data:
            if not row.get("gl_entry"):
                response.append(row)
            elif row.get("party") in self.customer_names:
                response.append(row)
                
        return response

        
def process_kwargs(doctype, *args, **kwargs):
    """Process and modify filters based on user permissions"""
    gen_filters = GenFilters(doctype, *args, **kwargs)

    if not gen_filters.custom_permission:
        return
        
    # Ensure filters exists in kwargs
    if "filters" not in kwargs:
        kwargs["filters"] = []
    
    # Handle Customer doctype specifically
    if doctype == gen_filters.perm_doctype:
        if gen_filters.customer_names:
            kwargs["filters"].append(["name", "in", gen_filters.customer_names])
        return
    if doctype == "GL Entry":
            kwargs["filters"].append(["owner", "=", frappe.session.user])

    # Handle other doctypes with customer links
    customer_filter = gen_filters.get_instances_has_customer()
    if customer_filter:
        kwargs["filters"].append(customer_filter)
