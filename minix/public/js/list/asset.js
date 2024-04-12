frappe.listview_settings['Asset'] = {
    onload: function (listview) {
        listview.page.add_inner_button(__('Run Depreciation'), function () {
            frappe.confirm('Are you sure you want to proceed?',
                () => {
                    frappe.call({
                        method: "minix.minix.methods.assets.schedule_asset_depreciation",
                        type: "POST",
                        callback: function (response) {
                            frappe.show_alert({
                                message: __('Asset Depreciation Scheduled Successfully'),
                                indicator: 'green'
                            });
                        }
                    });
                }, () => {
                    frappe.show_alert({
                        message: __('Action Cancelled'),
                        indicator: 'orange'
                    });
                })
        }
        );
    }
};