from django.test import Client

class KALiteClient(Client):
    
    def login(self, username, password, facility):

        self.get("/securesync/login/")
        
        data = {
            "csrfmiddlewaretoken": self.cookies["csrftoken"].value,
            "facility": facility,
            "username": username,
            "password": password,
        }
        
        response = self.post("/securesync/login/", data=data)
        
        return response.status_code == 302
