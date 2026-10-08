# SumUp and direct SEPA payments

Production website: https://la-premiere-brique.com

## Railway configuration

Set these variables on the Django web service (not the database):

- SUMUP_API_KEY: secret API key from the production SumUp account.
- SUMUP_MERCHANT_CODE: merchant code belonging to that same account.
- CARD_PAYMENTS_ENABLED=true
- SITE_URL=https://la-premiere-brique.com

Set the receiving bank details in Railway as well; they are deliberately not stored in Git:

- BANK_TRANSFER_ACCOUNT_HOLDER=<value provided by the account owner>
- BANK_TRANSFER_IBAN=<value provided by the account owner>
- BANK_TRANSFER_BIC=<value provided by the account owner>
- BANK_TRANSFER_BANK_NAME=<value provided by the account owner>

Remove stale bank overrides or update all four together. Keep secrets out of Git and chat.

The application creates Hosted Checkouts. It automatically sets:
- redirect_url: /payments/sumup/return/?transaction_id=...
- return_url (server webhook): /payments/sumup/webhook/?transaction_id=...

No manual webhook signing secret is needed. Webhook payloads are untrusted; the server fetches the checkout using its secret API key and verifies checkout ID, reference, merchant, EUR currency, and exact amount before crediting a deposit. Duplicate notifications update the same locked database row.

## Bank reconciliation

An investor enters an amount, then receives a unique PB- reference and the bank details. This creates a PENDING deposit, not spendable money.

After checking the actual bank statement, open Django Admin > Wallet transactions, match reference and amount, select the transfer, and use "Confirmer les virements reçus sur le compte bancaire". The action only confirms pending manual deposits and records the administrator and timestamp. Never confirm from a customer screenshot alone.

## Mollie migration

New checkouts no longer use Mollie. Old payment rows are retained. Existing Mollie return/webhook endpoints and MOLLIE_API_KEY remain temporarily for settling payments initiated before migration. Remove/revoke the Mollie key only after pending payments are reconciled. No new Mollie checkout can be started.

## Launch checks

1. Set the Railway variables and deploy this revision.
2. Confirm the deployment is healthy and both payment options appear for a logged-in account.
3. Test the complete card flow with a SumUp sandbox merchant first, or have the account owner perform a controlled live payment after launch.
4. Verify a paid deposit appears exactly once and a failed/unpaid payment gives no wallet credit.
5. Verify the configured transfer details and that preparing a transfer leaves the wallet unchanged.
6. Confirm actual receipt in the bank before using the admin action.
