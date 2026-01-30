backend architectury

Auth and logging - 
we need to implement two ways to sign in and sign up

if it's an sign up
	the request will come to backend with parameters that 
	will represent registration data, some profile informations, and specially type of profile, like - worker, business or individual(we have three types of accounts) Basically we have same oportunities for business or individual, but we need to register them like that.

	if it is worker - there should be only
		FullName
		number of the phone
		email
		password
		type of profile - (worker/business/individual)

	if it is business
		there should be -
		name of the company
		BIN
		INN
		Legal Adress
		Contact Name
		contact number
		Email
		Password
		type of profile - (worker/business/individual)

	if it is individual there should be
		FullName - (ФИО по русскому)
		Phone NUmber
		Email
		Password

if its Sign UP
there is universal thing for everyone
Email and Password

to show that user is logged in and do it very secure we need to -
implement JWT TOKEN

for the Flutter App
we need to implement silent refresher mechanism through Http Interceptor.
Btw we need to store tokens in the flutter secure storage(package)
