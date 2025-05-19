# # Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# # License: MIT. See LICENSE

# """build query for doclistview and return results"""

# import json
# from functools import lru_cache

# from sql_metadata import Parser

# import frappe
# import frappe.permissions
# from frappe import _
# from frappe.core.doctype.access_log.access_log import make_access_log
# from frappe.model import child_table_fields, default_fields, get_permitted_fields, optional_fields
# from frappe.model.base_document import get_controller
# from frappe.model.db_query import DatabaseQuery
# from frappe.model.utils import is_virtual_doctype
# from frappe.utils import add_user_info, cint, format_duration
# from frappe.utils.data import sbool


# def new_compress(data, args=None):
#     """separate keys and values"""
#     from frappe.desk.query_report import add_total_row

#     user_info = {}

#     if not data:
#         return data
#     if args is None:
#         args = {}
#     values = []
#     keys = list(data[0])

#     for row in data:
#         values.append([row.get(key) for key in keys])

#         # add user info for assignments (avatar)
#         if row.get("_assign", ""):
#             for user in json.loads(row._assign):
#                 add_user_info(user, user_info)

#     if args.get("add_total_row"):
#         meta = frappe.get_meta(args.doctype)
#         values = add_total_row(values, keys, meta)

#     return {"keys": keys, "values": values, "user_info": user_info}
