# https://www.tutorialspoint.com/python_network_programming/python_pop3.htm

# What needs to be done: https://support.google.com/accounts/answer/185833

import poplib

pop3server = 'pop.gmail.com'
username = '...@gmail.com'
password = '...'
pop3server = poplib.POP3_SSL(pop3server) # open connection
print (pop3server.getwelcome()) #show welcome message
pop3server.user(username)
pop3server.pass_(password)
pop3info = pop3server.stat() #access mailbox status
mailcount = pop3info[0] #toral email
print("Total no. of Email : " , mailcount)
print ("\n\nStart Reading Messages\n\n")
for i in range(2):
    for message in pop3server.retr(i+1)[1]:
        print (message)
pop3server.quit()