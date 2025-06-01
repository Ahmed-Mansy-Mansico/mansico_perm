
import json
import typing
from urllib.parse import quote

import frappe
import frappe.defaults
import frappe.desk.form.meta
import frappe.utils
from frappe import _, _dict
from frappe.desk.form.document_follow import is_document_followed
from frappe.model.utils.user_settings import get_user_settings
from frappe.permissions import check_doctype_permission, get_doc_permissions
from frappe.utils.data import cstr


if typing.TYPE_CHECKING:
    from frappe.model.document import Document

from frappe.desk.form.load import run_onload, get_docinfo, set_link_titles
from mansico_perm.permissions import GenFilters

@frappe.whitelist()
def getdoc(doctype, name):
    """
    Loads a doclist for a given document. This method is called directly from the client.
    Requries "doctype", "name" as form variables.
    Will also call the "onload" method on the document.
    """

    if not (doctype and name):
        raise Exception("doctype and name required!")

    try:
        doc = frappe.get_doc(doctype, name)
    except frappe.DoesNotExistError:
        check_doctype_permission(doctype)
        frappe.clear_last_message()
        return []
    gen_filters = GenFilters(doctype, {}, {})

    if gen_filters.field_name and gen_filters.customer_names and gen_filters.custom_permission:
        if doc.get(gen_filters.field_name) not in gen_filters.customer_names:
            raise frappe.PermissionError(("read", doctype, name))
        
    if not doc.has_permission("read"):
        check_doctype_permission(doctype)
        frappe.flags.error_message = _("Insufficient Permission for {0}").format(
            frappe.bold(_(doctype) + " " + name)
        )
        raise frappe.PermissionError(("read", doctype, name))
    # Replace cache if stale one exists
    # PERF: This should be eventually removed completely when we are sure about caching correctness
    if (key := frappe.can_cache_doc((doctype, name))) and frappe.cache.exists(key):
        frappe._set_document_in_cache(key, doc)

    run_onload(doc)
    doc.apply_fieldlevel_read_permissions()

    # add file list
    doc.add_viewed()
    get_docinfo(doc)

    doc.add_seen()
    set_link_titles(doc)
    if frappe.response.docs is None:
        frappe.local.response = _dict({"docs": []})
    frappe.response.docs.append(doc)


from mansico_perm.permissions import process_kwargs
from frappe.model.db_query import DatabaseQuery

def execute(doctype, *args, **kwargs):
    process_kwargs(doctype, *args, **kwargs)
    return DatabaseQuery(doctype).execute(*args, **kwargs)


from mansico_perm.permissions import GenFilters

def normalize_result(result, columns):
    # Converts to list of dicts from list of lists/tuples
    data = []
    column_names = [column["fieldname"] for column in columns]
    if result and isinstance(result[0], list | tuple):
        for row in result:
            row_obj = {}
            for idx, column_name in enumerate(column_names):
                row_obj[column_name] = row[idx]
            data.append(row_obj)
    else:
        data = result
    gen_filters = GenFilters("Report")
    if gen_filters.custom_permission:
        data = gen_filters.refactor_data(data)
    return data


def monkey_patchs():
    # \\beta-erp.dms-ksa.com\sharing\frappe14\apps\frappe\frappe\desk\form\load.py
    import frappe.desk.form.load
    frappe.desk.form.load.getdoc = getdoc
    # \\beta-erp.dms-ksa.com\sharing\frappe14\apps\frappe\frappe\desk\reportview.py
    import frappe.desk.reportview
    frappe.desk.reportview.execute = execute
    # \\beta-erp.dms-ksa.com\sharing\frappe14\apps\frappe\frappe\desk\query_report.py
    import frappe.desk.query_report
    frappe.desk.query_report.normalize_result = normalize_result
