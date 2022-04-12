# <========== Import Libraries ==========>
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import messaging

# <========== Initialize firebase ==========>
cred = credentials.Certificate('functions/firebase/firebaseKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()


def MakeDeposit(uniqueID, amount):

    transaction = db.transaction()
    ProcessDeposit(transaction, uniqueID, amount, SendDepositNotification)


@firestore.transactional
def ProcessDeposit(transaction, uniqueID, amount, callback):

    # Read data
    snapshot = db.collection(u'users').where(
        u'depositID', u'==', uniqueID).get(transaction=transaction)

    # Record the user notification tokens
    notificationTokens = snapshot[0].to_dict()["notificationTokens"]

    # Record the user's notifications
    notifications = snapshot[0].to_dict()["notifications"]
    notifications.append(
        'Deposit: Incoming deposit of R{}'.format(amount))

    # Record the user's ID
    userID = snapshot[0].id

    # Record the deposit
    transaction.set(db.collection(u'deposits').document(), {
        u'amount': amount,
        u'date': datetime.datetime.now(tz=datetime.timezone.utc),
        u'userID': snapshot[0].id
    })

    # Update the user's balance
    transaction.update(db.collection(u'users').document(snapshot[0].id), {
        u'balance': snapshot[0].to_dict()["balance"] + amount,
        u'notifications': notifications
    })

    callback(amount, notificationTokens, notifications, userID)


def SendDepositNotification(amount, notificationTokens, notifications, userID):

    for token in notificationTokens:

        try:

            message = messaging.Message(
                notification=messaging.Notification(
                    title='Deposit',
                    body='Incoming deposit of R{:.2f}'.format(amount)
                ),
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default'),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(sound='default'),
                    ),
                ),
                token=token)

            response = messaging.send(message)

            print('Successfully sent message:', response)

        except Exception:

            print("Token not found")
