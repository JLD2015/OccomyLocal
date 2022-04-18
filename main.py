# <========== Imports ==========>
import datetime
from datetime import date
from datetime import timedelta
import glob
import functions.firebase.firebase as Firebase
import os
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Execute this module dirrectly
if __name__ == "__main__":

    # <========== Downloads directory ==========>
    downloadsDirectory = "/Users/jmd/Downloads"

    # <========== Setup ==========>

    # Get withdrawals data
    withdrawalData, withdrawalIDs = Firebase.GetWithdrawals()

    # Generate file for Mercantile website
    paymentData = pd.DataFrame(columns=["A", "B", "C", "D", "E", "F"])
    branchCodes = {
        "ABSA": "632005",
        "Capitec": "470010",
        "FNB": "254005",
        "Nedbank": "198765",
        "Standard Bank": "051001"
    }

    counter = 0
    totalAmount = 0
    for withdrawal in withdrawalData:

        # Get the details for the user in question
        data = Firebase.GetUserDetails(withdrawal["userID"])
        bankName = data["bankName"]
        accountNumber = data["bankAccountNumber"]
        amount = round(withdrawal["amount"], 2)
        depositID = data["depositID"]
        userName = data["name"]

        # Insert row for individual payment
        paymentData.loc[counter] = [
            branchCodes[bankName],
            accountNumber,
            amount,
            "Occomy (Pty) Ltd", "Wit: " + depositID,
            userName[0:15]
        ]
        counter += 1
        totalAmount += amount

    paymentData.to_csv(
        downloadsDirectory +
        '/occomypayments.csv',
        index=False,
        header=False
    )

    # <========== Setup webdriver ==========>

    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": "/Users/jmd/Downloads",
             "detach": True}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), chrome_options=options)
    timeout = 300

    # Get to the login page
    driver.get("https://www.mercantile.co.za/business-internet-banking#")

    element_present = EC.presence_of_element_located((
        By.LINK_TEXT, "LOG IN"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(by=By.LINK_TEXT, value="LOG IN")
    element.click()

    element_present = EC.presence_of_element_located((
        By.XPATH, "(//a[contains(text(),'LOG IN')])[2]"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(
        by=By.XPATH, value="(//a[contains(text(),'LOG IN')])[2]")
    element.click()

    # Sign in
    element_present = EC.presence_of_element_located((
        By.XPATH, "//input[@id='textUsername']"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(
        by=By.XPATH, value="//input[@id='textUsername']")
    element.send_keys("13051725")

    element = driver.find_element(
        by=By.XPATH, value="//input[@id='textPassword']")
    element.send_keys("Horvath1029!")

    element = driver.find_element(
        by=By.XPATH, value="//input[@id='textMaidenname']")
    element.send_keys("Britz")

    element = driver.find_element(
        by=By.XPATH, value="//div[@id='login-wrapper']/button")
    element.click()

    time.sleep(20)

    # <========== Process withdrawals ==========>

    if len(withdrawalData) > 0:

        print("<========== Processing Withdrawals ==========>")

        # Enter the batch payment details
        element_present = EC.presence_of_element_located((
            By.XPATH, "//li[2]/a/i"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//li[2]/a/i")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='ft-tabs']/div[4]/h5"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='ft-tabs']/div[4]/h5")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//a[contains(text(),'Create Batch Schedule')]"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//a[contains(text(),'Create Batch Schedule')]")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='bulk-payments']/div[2]/form/div/div/div/select-account/div/div/div[2]/div"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='bulk-payments']/div[2]/form/div/div/div/select-account/div/div/div[2]/div")
        element.click()

        time.sleep(5)

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='account-item-0']/div/div/div/div/h4"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='account-item-0']/div/div/div")
        element.click()

        time.sleep(5)

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='bulk-payments']/div[2]/form/div/div[2]/div/div/div[2]/label/span"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='bulk-payments']/div[2]/form/div/div[2]/div/div/div[2]/label/span")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//input[@name='beneficiaryRemarks']"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//input[@name='beneficiaryRemarks']")
        element.send_keys(date.today().strftime("%Y/%m/%d"))

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='bulk-payments']/div[2]/form/div/div[2]/div/div[2]/div[3]/label/span"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='bulk-payments']/div[2]/form/div/div[2]/div/div[2]/div[3]/label/span")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//input[@id='amount']"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//input[@id='amount']")
        element.send_keys(totalAmount)

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='bulk-payments']/div[2]/form/div/div[2]/div[3]/div/button[2]"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='bulk-payments']/div[2]/form/div/div[2]/div[3]/div/button[2]")
        element.click()

        # Upload the batch payments file

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='fund-transfer']/div[2]/div/div[2]/div[2]/div/div[2]/button[2]"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='fund-transfer']/div[2]/div/div[2]/div[2]/div/div[2]/button[2]")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='fund-transfer']/div[2]/div/div[2]/div[4]/div/div/button"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='fund-transfer']/div[2]/div/div[2]/div[4]/div/div/button")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//input[@id='hidden-input-tpye-file']"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//input[@id='hidden-input-tpye-file']")
        element.send_keys(downloadsDirectory + "/occomypayments.csv")

        element_present = EC.presence_of_element_located((
            By.XPATH, "//button[@id='file-submit']"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//button[@id='file-submit']")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='bulk_payments_release']/div/div/div/div[3]/div/div/button[2]"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='bulk_payments_release']/div/div/div/div[3]/div/div/button[2]")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='bulk_payments_release']/div/div[2]/div[2]/div[3]/div/button"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='bulk_payments_release']/div/div[2]/div[2]/div[3]/div/button")
        element.click()

        # Release the schedule
        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='schedule-details']/div/div/div[3]/div/div[3]/div"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='schedule-details']/div/div/div[3]/div/div[3]/div")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='bulk_payments_release']/div/div/div[2]/div[3]/div/div/button[2]"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='bulk_payments_release']/div/div/div[2]/div[3]/div/div/button[2]")
        element.click()

        element_present = EC.presence_of_element_located((
            By.XPATH, "//div[@id='bulk_payments_release']/div/div[2]/div/div[2]/div/div/button"))
        WebDriverWait(driver, timeout).until(element_present)
        element = driver.find_element(
            by=By.XPATH, value="//div[@id='bulk_payments_release']/div/div[2]/div/div[2]/div/div/button")
        element.click()

    else:
        print(" <========== No withdrawals to process ==========>")

    # <========== Process Deposits ==========>

    print("<========== Processing Deposits ==========>")

    element_present = EC.presence_of_element_located((
        By.XPATH, "//li[5]/a/i"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(
        by=By.XPATH, value="//li[5]/a/i")
    element.click()

    element_present = EC.presence_of_element_located((
        By.XPATH, "//div[@id='interim']/form/div[2]/div/div/select-account/div/div/div[2]/div"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(
        by=By.XPATH, value="//div[@id='interim']/form/div[2]/div/div/select-account/div/div/div[2]/div")
    element.click()

    time.sleep(5)

    element_present = EC.presence_of_element_located((
        By.XPATH, "//div[@id='account-item-0']/div/div/div/div/h5/span"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(
        by=By.XPATH, value="//div[@id='account-item-0']/div/div/div/div/h5/span")
    element.click()

    time.sleep(5)

    element_present = EC.presence_of_element_located((
        By.XPATH, "//div[@id='interim']/form/div[2]/div/div[2]/div/div[2]/div[2]/label/span"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(
        by=By.XPATH, value="//div[@id='interim']/form/div[2]/div/div[2]/div/div[2]/div[2]/label/span")
    element.click()

    element_present = EC.presence_of_element_located((
        By.XPATH, "//button[@id='ft-proceed']"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(
        by=By.XPATH, value="//button[@id='ft-proceed']")
    element.click()

    element_present = EC.presence_of_element_located((
        By.XPATH, "//button[@id='btn-download']"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(
        by=By.XPATH, value="//button[@id='btn-download']")
    element.click()

    time.sleep(20)

    # <========== Close the webdriver ==========>
    element_present = EC.presence_of_element_located((
        By.XPATH, "//li[6]/i"))
    WebDriverWait(driver, timeout).until(element_present)
    element = driver.find_element(
        by=By.XPATH, value="//li[6]/i")
    element.click()
    driver.close()

    # <========== Mark withdrawals as processed ==========>

    for id in withdrawalIDs:
        Firebase.MarkWithdrawalAsProcessed(id)

    # Delete the withdrawals document
    os.remove(downloadsDirectory + "/occomypayments.csv")

    # <========== We need to process deposits ==========>

    # Clean the downloaded data

    listOfFiles = glob.glob(downloadsDirectory + "/*")
    latestFile = max(listOfFiles, key=os.path.getctime)
    dirtyData = pd.read_csv(latestFile, header=1)

    dirtyData.drop(["Account", "Description", "Fees",
                   "Balance"], axis=1, inplace=True)
    dirtyData.drop(dirtyData.tail(1).index, inplace=True)
    dirtyData = dirtyData.iloc[:, :-1]
    dirtyData.dropna(subset=['Amount'], inplace=True)

    dirtyData['Date'] = pd.to_datetime(dirtyData['Date'])
    dateYesterday = date.today() - timedelta(days=1)
    dirtyData = dirtyData.loc[dirtyData["Date"]
                              == dateYesterday.strftime("%Y-%m-%d")]
    cleanData = dirtyData

    print(cleanData)

    # Make deposits
    for index, row in cleanData.iterrows():
        Firebase.MakeDeposit(row["Reference"].strip(), row["Amount"])

    # Delete the statement
    os.remove(latestFile)

    # <========== At the end of the month process conversion requests ==========>
    currentDate = datetime.datetime.today().day

    if (currentDate == 18):
        Firebase.ProcessConversionRequests()
