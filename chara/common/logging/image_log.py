import base64

class ImageLogItem:
    @staticmethod
    def bytes_to_img_tag(png_bytes: bytes) -> str:
        b64 = base64.b64encode(png_bytes).decode("ascii")
        return f'<img src="data:image/png;base64,{b64}">'