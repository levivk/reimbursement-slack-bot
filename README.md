# reimbursement-slack-bot

A slack bot for forwarding receipts to the payment processor and tracking reimbursement status

## TODO
- [x] Send email with attachment
- [x] Test Melio for setting vendor and invoice number thru picture
  - Just use white header. Might work sometimes, but receipt detection is too good.
- [ ] Use opencv to modifiy image accordingly
- [ ] Listen for messages on channel and get attachment
  - [ ] Look in thread for attachment if not on main post
  - [ ] respond with invoice number and record post for invoice
- [ ] listen for emails and respond to post once payment confirmation is received


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