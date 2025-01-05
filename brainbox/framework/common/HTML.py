class HTML:
    @staticmethod
    def escape_code(code):
        code = (
            code
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('&', "&amp;")
            .replace(" ", "&nbsp")
            .replace("\n", "<br>")
        )
        return code