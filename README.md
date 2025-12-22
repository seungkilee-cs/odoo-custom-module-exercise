# Odoo Custom Module Exercise

Customizing Odoo ERP Modules for implementation of sales-purchase app records links, creating PO directly from SO screen, and smart button to navigate between the linked records across the two apps.

## Requirements

- [x] 1. On the Sales Order record, be able to create a Purchase order that uses the same product and quantity as the Sales Order
- [x] 2. Create PO button is invisible after the initial PO creation from the Sales Order. (Purchase Order seems to have one to one relationship to sales order, but cannot infer the DB details from the purchase order. It makes sense, but for now we can just have the button hidden once there are at least one Purchase Order for Sales Order.)
- [x] 3. Edge Case Validations (null SO line, deposit as SO line, multi-item including invalid line)
- [x] 4. (Bonus) Add Smart Buttons to navigate between the Sales and Purchase Orders

## How to Run

1. Make sure Odoo 19.0 is installed
2. add odoo.conf in the root of the Odoo directory
3. git clone this repo
4. rename the repo to a custom module wrapper (like `custom_addon`)
5. in the odoo.conf add the addon
6. Start Odoo with your config `./odoo-bin -c odoo.conf`
7. In the App page, search for `sale_purchase_link` module (make sure to search for all, not just app)
![app_search](./assets/0__app_search.png)
8. once the module is found, upgrade it (or you can run it with `./odoo-bin -c odoo.conf -u sale_purchase_link` upon the odoo startup)
![module_search](./assets/0__module_search.png)

Here is an example of odoo.conf at the odoo root. make sure other db configs are present, and in the conf addons_path includes the original addons which should be `addons`, as well as the module `custom_addons`. You could also include the addons_path as a flag.

```odoo.conf
[options]
addons_path = {PATH_TO_ODOO}/odoo/addons,{PATH_TO_ODOO}/odoo/custom_addons
db_host = HOSTNAME
db_port = DBPORT
```

## Screenshots of the Workflow

### 0. Basic Validations
![null_validation](./assets/0_null_line_validation.png)
![deposit_validation](./assets/0_deposit_line_validation.png)

- disallow faulty data input by checking on Sales order line entry
- also checks for edge case of invalid order lines for the purchase order (deposit)

### 1. Create Purchase Order Button on a Sales Order Record
![create_new](./assets/1_create_valid_sales_order.png)
![created_new](./assets/2_multi_item_sales.png)

- "Create PO" button appears grouped with the other primary buttons
- test with multi-item Sales Order lines, including a valid Sales Order line (deposit) that is simulatneously invalid for Purchase Order line.

### 2. Purchase Order Created with same Product and Quantity
![purchase_order](./assets/3_multi_item_purchase_order_created.png)

- The Purchase Order Record Price is defaulted to 0
- The Purchase Order Record Vendor is defaulted based on business logic using product info or fallback
- Redirected to the PO page upon creation
- Once the PO is created, Smart Button appears for SO <-> PO Navigation (Sales Order Button)
- Can no longer see the "Create PO" button on Sales Order record.

### 3. (Bonus) Smart Buttons to Navigate between Sales Order and Purchase Order
![smart_button](./assets/4_purchase_order_button_default.png)

- Button only appears if there is a Purchase Order tied to the Sales Order (or vice versa)
- From the Sales Order Record, can navigate to PO using "Purchase" button (default behavior, but the full custom logic is in place in case we want to replace it)
- From the Purchase Order Record, can navigate to SO using "Sales Order" button (custom smart button implementation.)

![smart_button_calls](./assets/4_smart_button_navigation.png)
- Calls for the smart button navigation as it appears on the server side.
