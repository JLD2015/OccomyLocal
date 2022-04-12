# <========== Imports ==========>
from datetime import date
from datetime import timedelta
import glob
import functions.firebase.firebase as Firebase
import os
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Execute this module dirrectly
if __name__ == "__main__":

    # <========== Downloads directory ==========>
    downloadsDirectory = "/Users/jmd/Downloads"

    # <========== Handle deposits ==========>

    # Setup webdriver
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": "/Users/jmd/Downloads"}
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), chrome_options=options)

    # Get to the login page
    driver.get("https://www.mercantile.co.za/business-internet-banking#")
    element = driver.find_element(by=By.LINK_TEXT, value="LOG IN")
    element.click()
    time.sleep(5)

    element = driver.find_element(
        by=By.XPATH, value="(//a[contains(text(),'LOG IN')])[2]")
    element.click()
    time.sleep(5)

    # Sign in
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
        by=By.XPATH, value="//div[@id='login-wrapper']/button/b")
    element.click()
    time.sleep(30)

    # Download statement
    element = driver.find_element(
        by=By.XPATH, value="//li[5]/a/i")
    element.click()
    time.sleep(5)
    element = driver.find_element(
        by=By.XPATH, value="//div[@id='interim']/form/div[2]/div/div/select-account/div/div/div[2]/div")
    element.click()
    time.sleep(5)
    element = driver.find_element(
        by=By.XPATH, value="//div[@id='account-item-0']/div/div/div/div/h5/span")
    element.click()
    time.sleep(5)
    element = driver.find_element(
        by=By.XPATH, value="//div[@id='interim']/form/div[2]/div/div[2]/div/div[2]/div[2]/label/span")
    element.click()
    time.sleep(5)
    element = driver.find_element(
        by=By.XPATH, value="//button[@id='ft-proceed']")
    element.click()
    time.sleep(5)
    element = driver.find_element(
        by=By.XPATH, value="//button[@id='btn-download']")
    element.click()
    time.sleep(30)

    # Close the browser
    element = driver.find_element(
        by=By.XPATH, value="//li[6]/i")
    element.click()
    time.sleep(5)
    driver.close()

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

    # Make deposits
    for index, row in cleanData.iterrows():
        Firebase.MakeDeposit(row["Reference"].strip(), row["Amount"])

    # Delete the statement
    os.remove(latestFile)

    # <========== Handle Withdrawals ==========>
