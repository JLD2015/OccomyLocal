# <========== Imports ==========>
from datetime import date
from datetime import timedelta
import pandas as pd
import functions.firebase.firebase as Firebase

# Execute this module dirrectly
if __name__ == "__main__":

    # <========== Clean statement ==========>
    dirtyData = pd.read_csv("statement.csv", header=1)
    dirtyData.drop(["Account", "Description", "Fees",
                   "Balance"], axis=1, inplace=True)
    dirtyData.drop(dirtyData.tail(1).index, inplace=True)
    dirtyData = dirtyData.iloc[:, :-1]
    dirtyData.dropna(subset=['Amount'], inplace=True)

    # <========== Get transactions from yesterday ==========>
    dirtyData['Date'] = pd.to_datetime(dirtyData['Date'])
    dateYesterday = date.today() - timedelta(days=1)
    dirtyData = dirtyData.loc[dirtyData["Date"]
                              == dateYesterday.strftime("%Y-%m-%d")]

    # <========== Check whether we have transactions to process ==========>
    if (len(dirtyData.index) > 0):

        # Look for references which have a valid ID as a substring
        allDepositIDs = Firebase.getAllDepositIDs()
        for depositID in allDepositIDs:
            for index, row in dirtyData.iterrows():
                if depositID in row["Reference"]:
                    dirtyData.loc[index, 'Reference'] = depositID

        # At this point we can drop rows which are longer than 8 characters
        dirtyData = dirtyData[dirtyData['Reference'].isin(allDepositIDs)]

        # The data is now clean
        cleanData = dirtyData

        print(cleanData)

        # Make deposits
        for index, row in cleanData.iterrows():
            Firebase.MakeDeposit(row["Reference"].strip(), row["Amount"])

    else:
        print("No deposits yesterday")
