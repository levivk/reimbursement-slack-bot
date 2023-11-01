# reimbursement-slack-bot

A slack bot for forwarding receipts to the payment processor and tracking reimbursement status

## TODO
- [x] Send email with attachment
- [x] Test Melio for setting vendor and invoice number through picture
  - Just use white header. Might work sometimes, but receipt detection is too good.
- [x] Use opencv to modifiy image accordingly
  - [x] Add message to header
- [x] Listen for messages on channel and get attachment
  - [x] Look in thread for attachment if not on main post
  - [x] respond with invoice number and record post for invoice
- [x] switch to real channel
- [x] listen for emails and respond to post once payment confirmation is received


Image content:
- Name
- Bill #: 
- Date
- Message

Email content:
- Pay to: Name
- Bill #:
- Date
- Message
