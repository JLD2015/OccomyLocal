# <========== Import Libraries ==========>
import datetime
from email import feedparser
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import messaging
from tqdm import tqdm

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

            messaging.send(message)

        except Exception:

            print("Token not found")


def GetWithdrawals():

    docs = db.collection(u'withdrawals').where(
        u'processed', u'==', False).get()

    withdrawalData = []
    withdrawalIDs = []
    for doc in docs:
        withdrawalData.append(doc.to_dict())
        withdrawalIDs.append(doc.id)

    return withdrawalData, withdrawalIDs


def GetUserDetails(userID):
    data = db.collection(u'users').document(userID).get()
    return data.to_dict()


def MarkWithdrawalAsProcessed(withdrawalID):
    db.collection(u'withdrawals').document(
        withdrawalID).update({u'processed': True})


def ProcessConversionRequests():

    currentDate = datetime.datetime.today().day

    if (currentDate == 1):

        print("<========== Processing conversion requests ==========>\n")

        docs = db.collection(u'conversions').where(
            u'processed', u'==', False).get()

        for doc in docs:
            data = doc.to_dict()

            # Update the user to customer
            db.collection(u'users').document(
                data["userID"]).update({u'isMerchant': False})

            # Mark the conversion request as processed
            db.collection(u'conversions').document(
                doc.id).update({u'processed': True})


# <========== Used for cleaning uncomplete transactions ==========>
def cleanTransactions():
    docs = db.collection(u'transactions').where(
        u'status', u'==', u"pending").get()

    if len(docs) > 0:

        print("<========== Cleaning transactions ==========>\n")

        removeIDs = []
        for doc in docs:
            removeIDs.append(doc.to_dict()["transactionID"])
            db.collection(u'transactions').document(doc.id).delete()

        db.collection(u'transactions').document(u'transactionIDs').update(
            {u'transactionIDs': firestore.ArrayRemove(removeIDs)})

    else:
        print("<========== No transactions to clean ==========>\n")


# <========== Used for checking balance of system ==========>
def balanceSystem(bankTotal):

    totalBalance = 0
    totalFees = 0
    totalCashBack = 0

    docs = db.collection(u'users').get()

    for doc in docs:
        if doc.id != "apiKeys" and doc.id != "depositIDs":
            data = doc.to_dict()
            totalBalance += data["balance"]
            totalFees += data["fees"]
            totalCashBack += data["cashBack"]

    requiredTotal = totalBalance + totalFees

    print("<========== Balancing ==========>")
    print(f"\nTotal Balance: {round(totalBalance, 2)}")
    print(f"Total Fees: {round(totalFees, 2)}")
    print(f"Total Cashback: {round(totalCashBack, 2)} \n")
    print(f"Required Total: {round(requiredTotal, 2)}")
    print(f"Bank Total: {round(bankTotal, 2)} \n")

    if bankTotal >= requiredTotal:
        print("SYSTEM IN BALANCE \n")
    else:
        print("EMERGENCY: SYSTEM OUT OF BALANCE \n")

    db.collection(u"accounting").document(u"totals").set({
        datetime.datetime.now().strftime("%Y/%m/%d"): {
            u'totalBalance': round(totalBalance, 2),
            u'totalFees': round(totalFees, 2),
            u'totalCashBack': round(totalCashBack, 2),
            u'requiredTotal': round(requiredTotal, 2),
            u'bankTotal': round(bankTotal, 2)
        }
    })

    # We want to reset fees and cashback on the first of every month
    currentDate = datetime.datetime.today().day

    if (currentDate == 1):

        print("<========== Resetting fees and cashback ==========>\n")

        # Record my revenue for the month (totalFees - totalCashBack)
        revenue = (totalFees - totalCashBack)*(100/115)
        vat = (totalFees - totalCashBack)-revenue
        db.collection(u"accounting").document(u"revenue").set({
            datetime.datetime.now().strftime("%Y/%m/%d"): {
                u'revenue': revenue,
                u'VAT': vat
            }
        })

        # Reset fees and cash back for all users
        for doc in tqdm(docs):

            if doc.id != "apiKeys" and doc.id != "depositIDs":

                data = doc.to_dict()

                fees = data["fees"]
                cashBack = data["cashBack"]
                notificationTokens = data["notificationTokens"]

                # Notify user of cash back and fees for month
                for token in notificationTokens:

                    try:

                        message = messaging.Message(
                            notification=messaging.Notification(
                                title='Occomy',
                                body=f"You made R{round(cashBack, 2)} in cashback and paid R{round(fees, 2)} in fees last month."
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

                        messaging.send(message)

                    # Delete dead notification tokens
                    except Exception:

                        db.collection(u'users').document(doc.id).update(
                            {u'notificationTokens': firestore.ArrayRemove([token])})

                # Reset the fees, cashback and totalTransactions
                db.collection(u'users').document(doc.id).update(
                    {u'fees': 0, u'cashBack': 0, u'totalTransactions': 0})


# <========== Used for getting a list of all of the deposit IDs we have ==========>
def getAllDepositIDs():

    doc = db.collection(u'users').document("depositIDs").get()
    data = doc.to_dict()["depositIDs"]

    return data
