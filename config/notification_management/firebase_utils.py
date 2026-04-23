import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os

# i did change this :
# Initialize Firebase Admin (add your service account key)
'''CCOUNT_PATH = os.path.join(settings.BASE_DIR, 'serviceAccountKey.json')

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)'''

# to this :
def _initialize_firebase():
    if firebase_admin._apps:
        return True
    SERVICE_ACCOUNT_PATH = os.path.join(settings.BASE_DIR, 'serviceAccountKey.json')
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        print("serviceAccountKey.json not found. FCM notifications disabled.")
        return False
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
        firebase_admin.initialize_app(cred)
        return True
    except Exception as e:
        print(f"Firebase init failed: {e}")
        return False 
# until here

def send_fcm_notification(user, title, body, data=None):
    # this part is added by me
    if not _initialize_firebase():  
        return False
    # until here
    try:
        # Get user's FCM token
        fcm_token = user.fcm_token.token if hasattr(user, 'fcm_token') else None
        
        if fcm_token:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=fcm_token,
                android=messaging.AndroidConfig(
                    notification=messaging.AndroidNotification(
                        channel_id='smartfarm_notifications',
                        priority='high',
                        sound='default',
                    )
                ),
            )
            
            response = messaging.send(message)
            print(f"✅ FCM notification sent: {response}")
            return True
            
    except Exception as e:
        print(f"❌ FCM notification failed: {e}")
        return False