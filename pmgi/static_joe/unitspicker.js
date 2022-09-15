

/**
 * A class for controlling the form that allows the user to specify units.
 * Must link to an HTML file from which the layout will be loaded.
 * HTML File should contain:
 * - A form where the all the selects will be added as <li's>(with ID: unit_form)
 * - Buttons for: apply, revert, default, cancel (with IDs: unit_apply, unit_revert, unit_default, unit_cancel)
 */
class UnitFormView{

    constructor(htmlTargetDiv, html, valid_units, currentval, defaultval, set_callback, cancel_callback) {
        this.change_units_callback = set_callback;
        this.currentval = currentval;
        this.defaultval = defaultval;
        this.cancel_callback = cancel_callback;

        this.unit_form_name = "unit_form";
        this.button_apply_name = "unit_apply";
        this.button_revert_name = "unit_revert";
        this.button_default_name = "unit_default";
        this.button_cancel_name = "unit_cancel";

        // Select the target div and load the html
        this.target = $("#"+htmlTargetDiv);
        this.target.load(html, ()=>{

            this.unit_form = $('#'+this.unit_form_name, this.target);

            // Attach the apply, revert and cancel buttons
            this.button_apply = $('#'+this.button_apply_name, this.target);
            this.apply_onclick = this.apply_onclick.bind(this);
            this.button_apply.on("click", this.apply_onclick);

            this.button_revert = $('#'+this.button_revert_name, this.target);
            this.revert_onclick = this.revert_onclick.bind(this);
            this.button_revert.on("click", this.revert_onclick);

            this.button_default = $('#'+this.button_default_name, this.target);
            this.default_onclick = this.default_onclick.bind(this);
            this.button_default.on("click", this.default_onclick);

            this.button_cancel = $('#'+this.button_cancel_name, this.target);
            this.cancel_onclick = this.cancel_onclick.bind(this);
            this.button_cancel.on("click", this.cancel_onclick);

            this.init(valid_units, this.currentval);
        });
    }

    /**
     * Create the selects for the unit form
     * @param valid_units Expects an Object with keys of the unit categories
     *                      and values of arrays of the allowable unit values
     *                      for that unit category
     * @param current_values Expects an Object with keys of the unit categories
     *                          and values of the current unit for that unit
     *                          category
     */
    init(valid_units, current_values){

        // Loop over all the configured unit types
        Object.keys(valid_units).forEach(unit_cat => {
            // The form will be a list of labelled select boxes
            let $li = $("<li>")
            let capital_name = unit_cat.charAt(0).toUpperCase() + unit_cat.slice(1);
            let $label = $('<label>'+capital_name+'</label>', {});
            let $select = $('<select/>', {'name': unit_cat});

            // Loop over each valid unit within the given unit category
            valid_units[unit_cat].forEach(unit_opt => {
                // Add an option to the select that corresponds to it
                $select.append($("<option>").val(unit_opt).text(unit_opt));
            });
            
            // Add the objects to the form
            this.unit_form.append($li.append($label).append($select));
        });
        // Set all the values
        this.set_values(current_values);
    }

    /**
     * Set the active values of the selects
     * @param units - a dict keyed by unit category and string values
     */
    set_values(units){
        // Copy the values from a dict
        Object.keys(units).forEach(key => {
            let selobj = $('[name="'+key+'"]', this.target);
            selobj.val(units[key]);
        });
    }

    /**
     * Get the current values in the form
     * @returns dict keyed by unit category, with string values for the selection
     */
    get_values(){
        // Convert the values to a dict
        return Object.fromEntries(new FormData(this.unit_form[0]));
    }

    /**
     * User clicks the apply button
     * @returns {boolean}
     */
    apply_onclick(){
        // Confirm
        let success = confirm('Changing the units will reset all data. Are you sure?');
        if(success){
            // Pass the units to the controller
            this.change_units_callback(this.get_values())
        } else {
            // do nothing and let the user figure it out
            return false;
        }
    }

    /**
     * User clicks the revert button
     */
    revert_onclick(){
        // revert back to what was set previously
        this.set_values(this.currentval);
    }

    /**
     * User clicks the default button
     */
    default_onclick(){
        this.set_values(this.defaultval);
    }

    /**
     * User clicks the cancel button
     * @returns {boolean}
     */
    cancel_onclick(){
        this.revert_onclick();
        this.cancel_callback()
    }
}
