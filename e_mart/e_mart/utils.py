import base64
import frappe

@frappe.whitelist()
def generate_barcodes(in_val):
	from io import BytesIO

	from barcode import Code128
	from barcode.writer import ImageWriter

	stream = BytesIO()
	Code128(str(in_val), writer=ImageWriter()).write(
		stream,
		{
			"module_height": 3,
			"text_distance": 0.9,
			"write_text": False,
		},
	)
	barcode_base64 = base64.b64encode(stream.getbuffer()).decode()
	stream.close()

	return barcode_base64