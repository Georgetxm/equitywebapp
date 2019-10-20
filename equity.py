from requests_oauthlib import OAuth2Session
from flask import Flask, render_template, redirect, url_for, request, session
from requests.auth import HTTPBasicAuth
import requests
import json
import random
from plot import plotGraph, plotPieChart
import pyrebase
from datetime import datetime, timedelta

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'fidor secret key'

client_id = "fidor client id"
client_secret = "fidor client secret"

authorization_base_url = 'https://apm.tp.sandbox.fidor.com/oauth/authorize'
token_url = 'https://apm.tp.sandbox.fidor.com/oauth/token'
redirect_uri = 'http://localhost:5000/callback'


fireBaseConfig = {
    "apiKey": "firebase api key",
    "authDomain": "security-ownership.firebaseapp.com",
    "databaseURL": "https://security-ownership.firebaseio.com",
    "projectId": "security-ownership",
    "storageBucket": "security-ownership.appspot.com",
    "messagingSenderId": "1020290852729"
}

firebase = pyrebase.initialize_app(fireBaseConfig)

db = firebase.database()


@app.route('/', methods=["GET"])
@app.route('/index', methods=["GET"])
def default():

    #Step 1: User Application Authorization
    #Sending authorization client ID and client Secret to Fidor for authorization
    fidor = OAuth2Session(client_id,redirect_uri=redirect_uri)
    authorization_url, state = fidor.authorization_url(authorization_base_url)
    #State is used to prevent CSRF. keep this for later.
    session['oauth_state'] = state
    print("authorization URL is =" +authorization_url)
    return redirect(authorization_url)



@app.route("/callback", methods=["GET"])
def callback():
    try:
        #Step 2: Retrieving an access token.
        #The user has been redirected back from the provider to your registered
        #callback URL. With this redirection comes an authorization code included
        #in the redirect URL. We will use that to obtain an access token.
        fidor = OAuth2Session(state=session['oauth_state'])
        authorizationCode = request.args.get('code')
        body = 'grant_type="authorization_code&code='+authorizationCode+ \
        '&redirect_uri=' +redirect_uri+'&client_id='+client_id
        auth = HTTPBasicAuth(client_id, client_secret)
        token = fidor.fetch_token(token_url,auth=auth,code=authorizationCode,body=body,method='POST')

        #At this point you can fetch protected resources but let's save
        #the token and show how this is done from a persisted token
        session['oauth_token'] = token
        return redirect(url_for('.services'))

    # Prevent oauth_token error
    except KeyError:
        print("Key error in services-to return back to index")
        return redirect(url_for('default'))


# Main page, fetches top business US news and renders it
@app.route("/services", methods=["GET"])
def services():
    #Fetching a protected resource using an OAuth 2 token.
    try:
        token = session['oauth_token']
        url = "https://api.tp.sandbox.fidor.com/accounts"

        payload = ""
        headers = {
            'Accept': "application/vnd.fidor.de;version=1,text/json",
            'Authorization': "Bearer "+token["access_token"],
            'cache-control': "no-cache",
            'Postman-Token': "37fd228e-b611-4afe-b615-88702bc26a15"
            }

        response = requests.request("GET", url, data=payload, headers=headers)
        customersAccount = json.loads(response.text)
        session['fidor_customer'] = customersAccount

        # Retrieve top US business headlines
        news_url = "https://newsapi.org/v2/top-headlines"

        news_querystring = {"country":"us","category":"business","apiKey":"346d2c3a1c3a4c69abf68e33624b6311"}

        news_payload = ""
        news_headers = {
            'cache-control': "no-cache",
            'Postman-Token': "07bfdeb7-256c-4b75-9672-9b5a776b42d4"
        }

        news_response = requests.request("GET", news_url, headers=news_headers, params=news_querystring)
        newsJSON = json.loads(news_response.text)
        news = newsJSON['articles']

        source = list()
        title = list()
        description = list()
        date = list()
        url = list()

        # Appending the news data to the relevant list
        try:
            for x in news:
                source.append(x['source']['name']) 
                title.append(x['title'])
                description.append(x['description'])
                date.append(x['publishedAt'][0:10])
                url.append(x['url'])
        except Exception:
            pass

        return render_template('equity.html', eNewsSource = source, eNewsTitle = title, eNewsDesc = description,
            eNewsDate = date, eNewsURL = url)

    except KeyError:
        print("Key error in services-to return back to index")
        return redirect(url_for('default'))


# To render the equity page after search
@app.route ('/result',methods=['GET','POST'])
def result():
    error = None
    if request.method == "POST":
        customersAccount = session['fidor_customer']
        customerDetails = customersAccount['data'][0]
        customerInformation = customerDetails['customers'][0]

        tickerCode = request.form['stockSymbol']

        # Refer to plot.py for graph plotting function that utilises 2 APIs - 
        # plotly to plot the candlestick chart with information form Alphavantage)
        # exception are to ignore erros that occurs after every plotted graph
        try:
            plotGraph(tickerCode)
        except Exception:
            pass

        url = "https://financialmodelingprep.com/api/company/profile/"+ tickerCode +""

        payload = ""
        headers = {
            'cache-control': "no-cache",
            'Postman-Token': "e0003f95-e8c6-4cea-8142-99336827454d"
        }

        response = requests.request("GET", url, data=payload, headers=headers)

        # API Returns JSON with <pre> tags at the front and back
        # removed the tags before formatting it as JSON
        stockData = json.loads(response.text[5:-5]) 

        # To get all relevant stock data
        name = stockData[tickerCode]["companyName"]
        latestStockPrices = stockData[tickerCode]["Price"]
        beta = stockData[tickerCode]["Beta"]
        avgVolume = stockData[tickerCode]["VolAvg"]
        changePerc = stockData[tickerCode]["ChangesPerc"]
        exchange = stockData[tickerCode]["exchange"]
        industry = stockData[tickerCode]["industry"]
        sector = stockData[tickerCode]["sector"]
        website = stockData[tickerCode]["website"]
        ceo = stockData[tickerCode]["CEO"]
        desc = stockData[tickerCode]["description"]

        # Used to change colour of card in HTML based on positive/negative changes
        if "+" in changePerc:
            positive = True
        else:
            positive = False

        # Used to get News from NEWSAPI 
        news_url = "https://newsapi.org/v2/everything"

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now()- timedelta(days=1)).strftime('%Y-%m-%d')

        news_querystring = {"q":tickerCode,"from":yesterday,"to":today,"sortBy":"popularity","apiKey":"346d2c3a1c3a4c69abf68e33624b6311"}

        news_payload = ""
        news_headers = {
            'cache-control': "no-cache",
            'Postman-Token': "07bfdeb7-256c-4b75-9672-9b5a776b42d4"
        }

        news_response = requests.request("GET", news_url, data=news_payload, headers=news_headers, params=news_querystring)
        newsJSON = json.loads(news_response.text)
        news = newsJSON['articles']

        source = list()
        title = list()
        description = list()
        date = list()
        url = list()

        # Appending the news data to the relevant list
        try:
            for x in news:
                source.append(x['source']['name']) 
                title.append(x['title'])
                description.append(x['description'])
                date.append(x['publishedAt'][0:10])
                url.append(x['url'])
        except Exception:
            pass

        return render_template('equity.html', tCode=tickerCode, sName = name,sPrice = latestStockPrices, 
            sBeta = beta, sVolume = avgVolume, sChangeP = changePerc, sPositive = positive,
            sExchange = exchange, sIndustry = industry, sSector = sector, sWebsite = website, sCEO =  ceo, 
            sDesc = desc, fFirstName = customerInformation["first_name"], fLastName = customerInformation["last_name"], 
            eBalance = (customerDetails['balance']/100), eNewsSource = source, eNewsTitle = title, eNewsDesc = description,
            eNewsDate = date, eNewsURL = url)


# To retrieve information of a FIDOR bank user
@app.route ('/user_profile', methods=['GET'])
def user():
    customersAccount = session['fidor_customer']
    customerDetails = customersAccount['data'][0]
    customerInformation = customerDetails['customers'][0]

    return render_template('user_profile.html', uBalance = (customerDetails["balance"]/100), uID = customerDetails["id"], uAccountNo = customerDetails["account_number"],
        uFirstName = customerInformation["first_name"], uLastName = customerInformation["last_name"], uEmail = customerInformation["email"],
        uAddress = (customerInformation["adr_country"] + ", " + customerInformation["adr_street"] + ", " + customerInformation["adr_street_number"]))


# To retrieve all transactions of a FIDOR bank user
@app.route ('/transactions', methods=['GET'])
def transactions():
    transaction_url = "https://api.tp.sandbox.fidor.com/transactions"
    token = session['oauth_token']

    headers = {
    'Accept': "application/vnd.fidor.de;version=1,text/json",
    'Content-Type': "application/json",
    'Authorization': "Bearer "+token["access_token"],
    'cache-control': "no-cache",
    'Postman-Token': "b3c54dc9-0f93-4126-9de2-4a138bf68f06"
    }

    response = requests.request("GET", transaction_url, headers=headers)
    jsonData = json.loads(response.text)
    transactionList = jsonData["data"]
    
    # Specific list to store each data, e.g. tID stores all the ID in a list
    tID = list()
    tDesc = list()
    tReceiver = list()
    tCurrency = list()
    tAmount = list()
    tDate = list()
    x = 0

    # Last transaction is always SEED money, not required to show it, thus -1
    # Appends data to their relevant list
    try:
        while (x < (len(transactionList)-1)):
            tID.append(transactionList[x]["id"])
            tDesc.append(transactionList[x]["transaction_type_details"]["remote_subject"])
            tReceiver.append(transactionList[x]["transaction_type_details"]["remote_name"])
            tCurrency.append(transactionList[x]["currency"])
            tAmount.append((transactionList[x]["amount"]/100))
            tDate.append(transactionList[x]["created_at"])
            x = x + 1
    except Exception:
        pass
       
    return render_template('transactions.html', tID = tID, tDesc = tDesc, tReceiver = tReceiver,
        tCurrency = tCurrency, tAmount = tAmount, tDate = tDate)


# To render the transfer page with relevant information for the customer 
# to make a transfer
@app.route("/bank_transfer", methods=["GET"])
def transfer():
    try:
        customersAccount = session['fidor_customer']
        customerDetails = customersAccount['data'][0]

        return render_template('transfer.html',fFIDORID=customerDetails["id"],
            fAccountNo=customerDetails["account_number"],fBalance=(customerDetails["balance"]/100))

    except KeyError:
        print("Key error in bank_transfer-to return back to index")
        return redirect(url_for('.index'))


# Processing for the bank transfer with FIDOR Bank API
@app.route("/process", methods=["POST"])
def process():
    if request.method == "POST":
        token =  session['oauth_token']         
        customersAccount = session['fidor_customer']
        customerDetails = customersAccount['data'][0]

        fidorID = customerDetails['id']
        custEmail = request.form['recipientEmailAdd']
        transferAmt = int(float(request.form['transferAmount'])*100)
        transferRemarks = request.form['transactionRemarks']
        transactionID = request.form['transactionID']

        url = "https://api.tp.sandbox.fidor.com/internal_transfers"

        payload = "{\n\t\"account_id\": \""+fidorID+"\",\n\t\"receiver\": \""+ \
                custEmail+"\",\n\t\"external_uid\": \""+transactionID+"\",\n\t\"amount\": "+ \
                str(transferAmt)+",\n\t\"subject\": \""+transferRemarks+"\"\n}\n"

        headers = {
            'Accept': "application/vnd.fidor.de; version=1,text/json",
            'Authorization': "Bearer "+token["access_token"],
            'Content-Type': "application/json",
            'cache-control': "no-cache",
            'Postman-Token': "6dc13ce9-5e6e-4ff6-bd7c-82508356c3a1"
            }

        response = requests.request("POST", url, data=payload, headers=headers)
        transactionDetails = json.loads(response.text)

        return render_template('transfer_result.html',fTransactionID=transactionDetails["id"],
                custEmail=transactionDetails["receiver"],fRemarks=transactionDetails["subject"],
                famount=(float(transactionDetails["amount"])/100),
                fRecipientName=transactionDetails["recipient_name"])


# Get portfolio composition from FireBase based on user's account ID
@app.route("/portfolio", methods=['GET'])
def getPortfolio():
    
    customersAccount = session['fidor_customer']
    customerDetails = customersAccount['data'][0]
    fidorID = customerDetails["id"]
    
    pEquity = list()
    pQuantity = list()
    pPurchaseValue = list()

    
    portfolio = (db.child('fidorID').child(fidorID).child("stocks_owned").get()).val()
    x = 0

    if (portfolio is not None):
        while (x < len(portfolio)):
           pEquity.append(list(portfolio)[x])
           equity = pEquity[x]
           portfolioSpecifics = ((db.child('fidorID').child(fidorID).child("stocks_owned").child(str(equity)).get()).val())
           pQuantity.append(portfolioSpecifics.get(list(portfolioSpecifics)[1]))
           pPurchaseValue.append(portfolioSpecifics.get(list(portfolioSpecifics)[0]))
           x = x + 1

        try:
            plotPieChart(pEquity, pPurchaseValue)
        except Exception:
            pass
    
    return render_template('portfolio.html', pEquity = pEquity, pQuantity = pQuantity, pPurchaseValue = pPurchaseValue)


# To record down Equity ownership information to firebase and
# POST transaction information to FIDOR API
# Render results of transfer
@app.route("/equity_process", methods=["POST"])
def equityProcess():
    if request.method == "POST":    
        token =  session['oauth_token']         
        customersAccount = session['fidor_customer']
        customerDetails = customersAccount['data'][0]
        fidorID = customerDetails["id"]
        
        # Request data of stock transaction to be recorded down in firebase
        quantity = request.form['eQuantity']
        tickerCode = request.form['abcTickerCode']
        fidorTransferAmt = str(int(float(request.form['eTA']))*100)
        transferAmt = str(int(float(request.form['eTA'])))
        brokerEmail = "1705535a@student.tp.edu.sg"
        transferRemarks = ("Purchase " + tickerCode + " stock from FIDOR Broker - Teo Xuan Ming")
        transactionID = str(random.randint(0,100000))
       

        # Storing all the stocks owned by an ID into a list        
        # GET to check if there is existing ownership of stock
        # SET if there isn't, UPDATE if there is 
        if ((db.child('fidorID').child(fidorID).child("stocks_owned").get()).val()) is not None:
            dbPortfolio = list((db.child('fidorID').child(fidorID).child("stocks_owned").get()).val())
            for stock in dbPortfolio:
                if (stock == tickerCode):
                    previousQuantity = (db.child("fidorID").child(fidorID).child("stocks_owned").child(tickerCode).child("quantity").get()).val()
                    previousCost = (db.child("fidorID").child(fidorID).child("stocks_owned").child(tickerCode).child("cost").get()).val()
                    db.child("fidorID").child(fidorID).child("stocks_owned").child(tickerCode).update({
                        "quantity": str(int(previousQuantity) + int(quantity)),
                        "cost": str(int(previousCost) + int(transferAmt))})
                    break
                else:
                    db.child("fidorID").child(fidorID).child("stocks_owned").child(tickerCode).set({
                    "quantity": quantity,
                    "cost":transferAmt})
        else:
            db.child("fidorID").child(fidorID).child("stocks_owned").child(tickerCode).child("quantity").set(quantity)
            db.child("fidorID").child(fidorID).child("stocks_owned").child(tickerCode).child("cost").set(transferAmt)
        
        # To POST to FIDOR API
        url = "https://api.tp.sandbox.fidor.com/internal_transfers"

        payload = "{\n\t\"account_id\": \""+fidorID+"\",\n\t\"receiver\": \""+ \
                brokerEmail+"\",\n\t\"external_uid\": \""+transactionID+"\",\n\t\"amount\": "+ \
                str(fidorTransferAmt)+",\n\t\"subject\": \""+transferRemarks+"\"\n}\n"

        headers = {
            'Accept': "application/vnd.fidor.de; version=1,text/json",
            'Authorization': "Bearer "+token["access_token"],
            'Content-Type': "application/json",
            'cache-control': "no-cache",
            'Postman-Token': "6dc13ce9-5e6e-4ff6-bd7c-82508356c3a1"
            }

        response = requests.request("POST", url, data=payload, headers=headers)
        transactionDetails = json.loads(response.text)

        # To use what was posted to render the results page
        fTransactionID=transactionDetails["id"]
        custEmail=transactionDetails["receiver"]
        fRemarks=transactionDetails["subject"]
        famount=(float(transactionDetails["amount"])/100)
        fRecipientName=transactionDetails["recipient_name"]
        return render_template('transfer_result.html',fTransactionID=fTransactionID,
                 custEmail=custEmail,fRemarks=fRemarks, famount=famount,fRecipientName=fRecipientName)

#Logout function // not working
@app.route('/logout')
def logout():
    session['oauth_token'] = False
    session['oauth_state'] = False
    session['fidor_customer'] = False
    session.clear()
    return redirect(url_for('default'))