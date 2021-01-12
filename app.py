from flask import Flask, request, render_template, session, redirect, url_for, flash
import requests
import json

app = Flask(__name__)
app.secret_key = "thisissecret"

def findOccurrences(s, ch):
	return [i for i, letter in enumerate(s) if letter == ch]

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/about")
def about():
	return render_template("about.html")

@app.route("/buyer_register")
def buyer_register():
	if "username" in session:
		return render_template("index.html", registerError = True)
	return render_template("buyer_register.html")

@app.route("/seller_register")
def seller_register():
	if "username" in session:
		return render_template("index.html", registerError = True)
	return render_template("seller_register.html")

@app.route("/handle_register_data", methods = ["POST"])
def handle_register_data():	
	bank_details = {
	    "bank_details_top_level" : 
	    (f"""
	    	{{"email":{request.form["paypal_email"]}}} 
		    """),
	}

	bank_response = requests.post("https://ipfs.infura.io:5001/api/v0/add", files = bank_details)
	bank_json = bank_response.json()
	bank_hash = bank_json["Hash"]

	# print("Bank hash: ", bank_hash)
	if request.form["buyer_type"] == "Seller":
		choices = request.form.getlist("choice") #QmT1K5H6iycMhymvv4zssutA4wuWk4DmYGS63HAHRSsPna
	else:
		choices = []

	# print("choices:\n", choices)

	user_details = {
	    "user_details_top_level" : 
	    (f"""
	    	{{"name":{request.form["name"]}}},
	    	{{"username":{request.form["username"]}}},
	    	{{"password":{request.form["password"]}}},
	    	{{"bank_hash":{bank_hash}}},
	    	{{"buyer_type":{request.form["buyer_type"]}}},
	    	{{"choices":{choices}}}  
		    """),
	}

	user_response = requests.post("https://ipfs.infura.io:5001/api/v0/add", files = user_details)
	user_json = user_response.json()
	user_hash = user_json["Hash"] #QmUMKQLVDngyHzUx1pC955UMGav2EC2SKaQUJj4v9rNQ9D

	return render_template("success.html", user_hash = user_hash)

@app.route("/dashboard")
def dashboard():
	if "username" in session:
		return render_template("dashboard.html", name = session["name"], uname = session["username"])
	return render_template("login.html", dashError = True)


@app.route("/login")
def login():
	return render_template("login.html")


@app.route("/handle_login_data", methods = ["GET", "POST"])
def handle_login_data():
	if request.method == "POST":
		session['username'] = request.form['user_hash']

		# retrieve user_details from ipfs block
		params = (
		("arg", request.form["user_hash"]),
		)
		response = requests.post("https://ipfs.infura.io:5001/api/v0/block/get", params = params)

		if response.status_code != 200:
			return render_template("login.html", error=True)

		# access password
		start_arr = findOccurrences(response.text, ':')[2]
		end_arr = findOccurrences(response.text, '}')[2]
		retrieved_pwd = response.text[start_arr+1:end_arr]

		if retrieved_pwd == request.form["password"]:
			# access name 
			start_name = findOccurrences(response.text, ':')[0]
			end_name = findOccurrences(response.text, '}')[0]
			retrieved_name = response.text[start_name+1:end_name]

			# access username
			start_uname = findOccurrences(response.text, ':')[1]
			end_uname = findOccurrences(response.text, '}')[1]
			retrieved_uname = response.text[start_uname+1:end_uname]

			#storing user details in session
			session["name"] = retrieved_name
			session["username"] = retrieved_uname

			return render_template("dashboard.html", name = retrieved_name, uname = retrieved_uname)
	
	return render_template("login.html", error=True) 

@app.route('/logout')
def logout():
   # remove the username from the session if it is there
   session.pop('username', None)
   return redirect(url_for('index'))


if __name__ == "__main__":
	app.run(debug=True)