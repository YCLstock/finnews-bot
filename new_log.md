PS D:\AI\finnews-bot> python scripts/run_email_test.py
INFO:core.delivery_manager:Delivery manager initialized with platforms: ['discord', 'email']
INFO:__main__:🚀 Starting Email Delivery Test...
INFO:__main__:📬 Test recipient: limyuha27@gmail.com
INFO:__main__:📄 Created mock subscription data.
INFO:__main__:📰 Created 2 mock articles for the test email.
INFO:__main__:🚚 Fetched the delivery manager.
INFO:__main__:✉️ Attempting to send the test email via delivery manager...        
INFO:__main__:   (This will use the SMTP settings from your environment variables)
INFO:core.delivery_manager:📤 Sending 2 articles via Email to user: test-use...   
INFO:core.delivery_manager:📧 Sending 2 articles to email: limyuha27@gmail.com    
ERROR:core.delivery_manager:SMTP send error: send_message() got an unexpected keyword argument 'to_addresses'
ERROR:core.delivery_manager:❌ Failed to send email to limyuha27@gmail.com: send_message() got an unexpected keyword argument 'to_addresses'
ERROR:__main__:❌ The delivery manager reported a failure in the sending process.
ERROR:__main__:   Details: 2 articles failed to send.
INFO:__main__:🏁 Email Delivery Test Finished.