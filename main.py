# <========== Imports ==========>
import functions.browser.browser as Browser
import functions.firebase.firebase as Firebase

# Execute this module dirrectly
if __name__ == "__main__":

    downloadsDirectory = "/Users/jmd/Downloads"

    # <========== Mercantile Interaction ==========>
    bankBalance = Browser.mercantileAPI(downloadsDirectory)

    # <========== Remove uncomplete transactions ==========>
    Firebase.cleanTransactions()

    # <========== Perform Balancing ==========>
    Firebase.balanceSystem(bankBalance)  # Need to run at month end

    # <========== At the end of the month process conversion requests ==========>
    Firebase.ProcessConversionRequests()
