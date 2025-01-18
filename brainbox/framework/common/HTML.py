import json

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

    @staticmethod
    def button(address, title, parameters, control_parameters: dict[str, str] | None = None, active=True):
        btn = f'<button '
        if not active:
            btn += 'disabled '  # Add the 'disabled' attribute if the button is inactive
        btn += f'''onClick="makeRequest('{address}','''
        btn += json.dumps(parameters).replace('"', "'")
        btn += ','
        if control_parameters is None:
            btn += '{}'
        else:
            btn += json.dumps(control_parameters).replace('"', "'")
        btn += f')">{title}</button>'
        return btn

    @staticmethod
    def page(title: str, content:str|list[str]):
        if isinstance(content, str):
            pass
        else:
            content = "\n".join(content)
        return HTML.header(title)+content+HTML.footer()

    @staticmethod
    def header(title):
        return f'''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>{title}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </style>
        </head>
        <body>
        
        '''

    @staticmethod
    def footer():
        return '''
        <script>
        function makeRequest(address, jsonParameters, inputs) {
            console.log("Sending")
            // Disable all buttons on the page
            const buttons = document.querySelectorAll('button');
            buttons.forEach(button => button.disabled = true);
            
            for (const [key, elementId] of Object.entries(inputs)) {
                const inputElement = document.getElementById(elementId);
                if (inputElement) {
                    jsonParameters[key] = inputElement.value;
                }
            }
            
            console.log(jsonParameters)

            // Send POST request
            fetch(address, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({"arguments":jsonParameters})
            })
            .then(response => {
                //buttons.forEach(button => button.disabled = false);
                window.location.reload();
            })
            .catch(error => {
                console.error('There was a problem with the fetch operation:', error);
                // Optionally re-enable buttons if there is an error
                buttons.forEach(button => button.disabled = false);
            });
        }
        </script>
        </body>
        </html>
        '''