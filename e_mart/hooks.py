app_name = "e_mart"
app_title = "E Mart"
app_publisher = "efeone"
app_description = "custom frappe app for electronics stores"
app_email = "info@efeone.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "e_mart",
# 		"logo": "/assets/e_mart/logo.png",
# 		"title": "E Mart",
# 		"route": "/e_mart",
# 		"has_permission": "e_mart.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/e_mart/css/e_mart.css"
app_include_js = "/assets/e_mart/js/sales_invoice.js"

# include js, css files in header of web template
# web_include_css = "/assets/e_mart/css/e_mart.css"
# web_include_js = "/assets/e_mart/js/e_mart.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "e_mart/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"Purchase Invoice" : "e_mart/custom_scripts/purchase_invoice/purchase_invoice.js",
	"Sales Invoice" : "e_mart/custom_scripts/sales_invoice/sales_invoice.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "e_mart/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "e_mart.utils.jinja_methods",
# 	"filters": "e_mart.utils.jinja_filters"
# }

# Installation
# ------------

after_install = "e_mart.setup.after_install"
after_migrate = "e_mart.setup.after_migrate"

# Uninstallation
# ------------

before_uninstall = "e_mart.setup.before_uninstall"
# after_uninstall = "e_mart.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "e_mart.utils.before_app_install"
# after_app_install = "e_mart.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "e_mart.utils.before_app_uninstall"
# after_app_uninstall = "e_mart.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "e_mart.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Serial and Batch Bundle": {
		"on_submit": [
			"e_mart.e_mart.custom_scripts.serial_and_batch_bundle.serial_and_batch_bundle.set_purchase_category_from_voucher",
			"e_mart.e_mart.custom_scripts.serial_and_batch_bundle.serial_and_batch_bundle.set_purchase_category_on_creation"
		]	
	},
	"Purchase Receipt": {
		"before_insert": "e_mart.e_mart.custom_scripts.purchase_order.purchase_order.fetch_purchase_category"
	},
	"Purchase Invoice": {
		"before_save": "e_mart.e_mart.custom_scripts.purchase_invoice.purchase_invoice.update_schema_discount_amount",
		"on_submit": "e_mart.e_mart.custom_scripts.purchase_invoice.purchase_invoice.on_submit"
	},
	"Sales Invoice": {
		"validate":[
			  "e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.validate_buyback_fields",
			  "e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.calculate_total_expense",
			  "e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.calculate_profit_for_commission",
			  "e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.generate_emi_schedule",
			  "e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.update_emi_amount"
		],
		"on_submit": [
			"e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.on_submit",
			"e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.map_commission_to_sales_team",

		],
		"before_save":[
			"e_mart.e_mart.custom_scripts.sales_invoice.sales_invoice.map_commission_to_sales_team"
		],
	},
	"Payment Entry" : {
		"on_submit" : "e_mart.e_mart.custom_scripts.payment_entry.payment_entry.update_down_payment_status"
	}
	
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"e_mart.tasks.all"
# 	],
# 	"daily": [
# 		"e_mart.tasks.daily"
# 	],
# 	"hourly": [
# 		"e_mart.tasks.hourly"
# 	],
# 	"weekly": [
# 		"e_mart.tasks.weekly"
# 	],
# 	"monthly": [
# 		"e_mart.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "e_mart.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "e_mart.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	'Purchase Invoice': 'e_mart.e_mart.custom_scripts.purchase_invoice_dashboard.purchase_invoice_dashboard.get_data'
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["e_mart.utils.before_request"]
# after_request = ["e_mart.utils.after_request"]

# Job Events
# ----------
# before_job = ["e_mart.utils.before_job"]
# after_job = ["e_mart.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"e_mart.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
