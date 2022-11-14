
/**
 * A class for controlling the form that allows the user to specify units.
 * Must link to an HTML file from which the layout will be loaded.
 * HTML File should contain:
 * - A form where the all the selects will be added as <li's>(with ID: unit_form)
 * - Buttons for: apply, revert, default, cancel (with IDs: unit_apply, unit_revert, unit_default, unit_cancel)
 */
class UnitFormView{

    constructor(target_sel, html, valid_units, currentval, defaultval, set_callback, cancel_callback) {
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
        this.$outer = target_sel;
        this.$outer.addClass("modal");

        this.$inner = $("<div></div>");
        this.$inner.addClass("modal-content");
        this.$outer.append(this.$inner);

        this.$inner.load(html, ()=>{
            this.unit_form = $('#'+this.unit_form_name, this.$outer);

            // Attach the apply, revert and cancel buttons
            this.button_apply = $('#'+this.button_apply_name, this.$outer);
            this.apply_onclick = this.apply_onclick.bind(this);
            this.button_apply.on("click", this.apply_onclick);

            this.button_revert = $('#'+this.button_revert_name, this.$outer);
            this.revert_onclick = this.revert_onclick.bind(this);
            this.button_revert.on("click", this.revert_onclick);

            this.button_default = $('#'+this.button_default_name, this.$outer);
            this.default_onclick = this.default_onclick.bind(this);
            this.button_default.on("click", this.default_onclick);

            this.button_cancel = $('#'+this.button_cancel_name, this.$outer);
            this.cancel_onclick = this.cancel_onclick.bind(this);
            this.button_cancel.on("click", this.cancel_onclick);

            this.get_values = this.get_values.bind(this);

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
            let selobj = $('[name="'+key+'"]', this.$outer);
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

    toggle(){
        this.$outer.toggle()
    }

}

// Messing with the layout of the DataTable
//https://stackoverflow.com/questions/38602873/datatables-button-and-search-box-position

class ModalSubstancePicker{
    static EVENT_CANCEL = "msp_cancel";
    static EVENT_APPLY = "msp_apply";

    // Hard code the column indexes
    static idi = 0;        // ID string
    static nami = 1;       // name
    static mwi = 2;        // molecular weight
    static coli = 3;       // collection
    static clsi = 4;       // class
    sTable;

    constructor(outer_div_id, html, initialdata) {
        this.$outer = $('#'+outer_div_id);
        this.$outer.addClass("modal");

        this.$inner = $("<div></div>");
        this.$inner.addClass("modal-content");
        this.$outer.append(this.$inner);

        this.$inner.load(html, ()=>{

            this.button_updatefilt_name = "filt_update";
            this.button_cancel_name = "selection_cancel";

            this.button_updatefilt = $('#'+this.button_updatefilt_name, this.$outer);
            this.update_filter = this.update_filter.bind(this);
            this.button_updatefilt.on("click", this.update_filter);

            this.button_cancel = $('#'+this.button_cancel_name, this.$outer);
            this.cancel = this.cancel.bind(this);
            this.button_cancel.on("click", this.cancel);

            this.data_ready(initialdata);
        });
    }


    // SEL_UPDATE_FILTER
    //      sel_update_filter()
    // This is a wrapper function for sTable.draw(), which provides access
    // to the global sTable object.  This is the callback function to update
    // the selector table based on the filter.
    update_filter(){
        this.sTable.draw();
    }


    // SEL_FILTER
    //      sel_filter(settings, data, dataIndex)
    // The filter function is used to apply the filter settings to each row
    // It returns true when the row should be included.  The template for
    // the filter function is specified by the DataTables interface.  The
    // only argument used is data, which is an array of the row values, used
    // to apply the filter.
    //
    // When SEL_FILTER returns true, the row will be included by the filter.
    // When SEL_FILTER returns false, the row will be excluded by the
    // filter.  The SEL_FILTER is applied as a callback to the DataTables in
    // the SEL_DATA_READY function.
    filter(settings, data, dataIndex){
        let mw = data[ModalSubstancePicker.mwi];
        let col = data[ModalSubstancePicker.coli];
        let cls = data[ModalSubstancePicker.clsi];

        let mw_min = parseFloat(document.getElementById('filt_mw_min').value);
        let mw_max = parseFloat(document.getElementById('filt_mw_max').value);
        let col_ = document.getElementById('filt_col').value;
        let cls_ = document.getElementById('filt_cls').value;

        return (isNaN(mw_min) || mw >= mw_min) &&
            (isNaN(mw_max) || mw <= mw_max) &&
            (col_ == '' || col == col_) &&
            (cls_ == '' || cls == cls_);
    }



    select(idstr){
        let ok = confirm("Changing the substance will clear all data. Do you want to proceed?")
        if (ok){
            change_substance(idstr)
        } else {
            // ignore
        }
    }


    // SEL_DATA_READY
    //      sel_data_ready()
    // The SEL_DATA_READY function is the callback function for when the
    // PMGI response comes back with the available substances.  It populates
    // the rows of the selector table row-by-row.
    //
    // SEL_DATA_READY is assigned as a callback to the sTable object in the
    // SEL_INIT function.
    data_ready(data){
        let substances = data;
        // Initialize the data table
        if (this.sTable === undefined) {
            this.sTable = new DataTable('#selector_table', {});
        }


        // Loop over each of the substances
        let rowi = 0
        for (let idstr in substances){
            let subst = substances[idstr];
            // Parse the name
            if (subst.nam.length>0){
                name = subst.nam[0];
            }else{
                name = '';
            }

            let idtag = $('<a class="clickable" href="#"></a>');
            idtag.append(idstr);

            // Add the row
            // ID, name, MW, collection, class
            this.sTable.row.add([idtag[0].outerHTML, name, subst.mw, subst.col, subst.cls]);

            rowi += 1;
        }

        $('tbody', this.$outer).on( 'click', "a", (clicked)=>{
            this.select(clicked.currentTarget.innerHTML);
        });

        // https://datatables.net/examples/plug-ins/range_filtering.html
        // Register the filter() function for selecting rows
        // This is JQuery obfuscation magic.
        $.fn.dataTable.ext.search.push(this.filter);

        // Adjust the column sizes to match the window
        this.sTable.columns.adjust().draw()
    }

    toggle(){
        this.$outer.toggle()
    }

    cancel(){
        this.toggle();
    }
}






