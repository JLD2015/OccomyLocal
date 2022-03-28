# <========== Import Libraries ==========>
import datetime
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# <========== Initialize firebase ==========>
cred = credentials.Certificate('functions/firebase/firebaseKey.json')
firebase_admin.initialize_app(cred)
db = firestore.client()


def MakeDeposit(uniqueID, amount):

    transaction = db.transaction()
    ProcessDeposit(transaction, uniqueID, amount)


@firestore.transactional
def ProcessDeposit(transaction, uniqueID, amount):

    # Read data
    snapshot = db.collection(u'users').where(
        u'depositID', u'==', uniqueID).get(transaction=transaction)

    # Record the deposit
    transaction.set(db.collection(u'deposits').document(), {
        u'amount': amount,
        u'date': datetime.datetime.now(tz=datetime.timezone.utc),
        u'userID': snapshot[0].id
    })

    # Update the user's balance
    transaction.update(db.collection(u'users').document(snapshot[0].id), {
        u'balance': snapshot[0].to_dict()["balance"] + amount
    })
