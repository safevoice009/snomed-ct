# Design Document: API Credit Wallet & Developer Checkout Hub

## 1. Credit Meter UI Component
- Component: `.api-credit-meter-badge` in the sandbox header strip.
- Data attributes: `data-credits="982"`, `data-max="1000"`.
- Action: Clicking "⚡ Top-Up" opens `#topup-checkout-modal`.

## 2. Top-Up Package Cards
- **Starter Pack**: ₹499 $\rightarrow$ 3,000 Inferences (₹0.166 / call).
- **Pro Pack**: ₹1,999 $\rightarrow$ 15,000 Inferences (₹0.133 / call).
- **Scale Pack**: ₹4,999 $\rightarrow$ 45,000 Inferences (₹0.111 / call).

## 3. Backend API Routes
- `GET /api/v1/billing/packages`: Returns available pricing packages.
- `GET /api/v1/billing/balance`: Returns active API key quota and remaining usage.
