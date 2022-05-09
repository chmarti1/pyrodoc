// *********************************************
// * PAGE CREATION OUTLINE
// *********************************************
// * * Create HTML Document
// * * Get Info from Pyromat
// * * * Create Units selector +
// * * * Create substance selector +
// * * Define Current Units +
// * * Initialize User-specified Data Model
// * * Initialize Plot
// * * * Compute steam dome/isolines
// * * * Initialize Point Trace
// * * * Create Plot Axis Selector
// * * Initialize Table
// * * Allow User Interaction
// * * * Create Points
// * * * Delete Points
// * * * Change Units
// * * * Change Substance
// * * * Change display options?





// *********************************************
// * MODEL
// *********************************************

/**
 * Class that can handle notifying listeners when a change occurs
 */
class Subject {
    // Based on https://webdevstudios.com/2019/02/19/observable-pattern-in-javascript/
    static EVENT_ID_NULL = null;

    constructor() {
        this.listeners = [];
    }

    /**
     * Add a listener to the object
     * @param listener - Object: must contain listener.update(source, event, data)
     */
    addListener(listener) {
        this.listeners.push(listener);
    }

    removeListener(listener) {
        const removeIndex = this.listeners.findIndex(obs => {
            return listener === obs;
        });

        if (removeIndex !== -1) {
            this.listeners = this.listeners.slice(removeIndex, 1);
        }
    }

    /**
     * Notify all listeners of events
     * @param source - Object: the origin object that created the event
     * @param event - String: an indicator of the event type (or null)
     * @param data - Various: data associated with the event (or null)
     */
    notify(source, event=Subject.EVENT_ID_NULL, data=null) {
        if (this.listeners.length > 0) {
            this.listeners.forEach(listener => listener.update(source, event, data));
        }
    }
}

/**
 * Class to hold data about the thermodynamic substance including a list of
 * values that has been computed
 */
class PointModel extends Subject{
    // Several event IDs thrown by this
    static EVENT_UNIT = 'unit'; // Data will be get_unit()
    static EVENT_SUBSTANCE = 'substance'; // Data will be get_substance()
    static EVENT_POINT_ADD = 'point_add' // Data will be the added point
    static EVENT_POINT_DELETE = 'point_delete' // Data will be id of deleted point
    static EVENT_INIT_POINTS = 'init_pts'; // Data will be null
    static EVENT_INIT_AUXLINE = 'init_aux'; // Data will be null
    static EVENT_AUXLINE_ADD = 'auxline_add'; // data will be the added line
    static EVENT_AUXLINE_DELETE = 'auxline_del'; // data will be the id of the deleted line

    DEFAULT_SUB_SHORTLIST=["mp.H2O","mp.C2H2F4","ig.air","ig.O2", "ig.N2"];
    DEFAULT_PROP_SHORTLIST=["T","p","v","e","h","s","x"];
    DEFAULT_SUBSTANCE = 'mp.H2O';
    INIT_PT_ID = 1;
    INIT_AUX_ID = 1;

    constructor() {
        super();
        // Init this.points and this.auxlines
        this.init_auxlines();
        this.init_points();

        // Current units, and all possible units
        this.units = null;
        this.valid_units = null;

        // Current substance and all possible substances
        this.substance = null;
        this.valid_substances = null;
    }

    /**
     * Initialize the valid units and substance lists
     * @param valid_units - dict of valid units, keys are unit category,
     *                          values are arrays of legal values
     * @param valid_substances - dict of valid substances, keys are the
     *                             substance id, values are a dict with info
     *                             from PMGI
     */
    init_info(valid_units, valid_substances){
        this.valid_units = valid_units;
        this.valid_substances = valid_substances;
    }

    /**
     * Clear all auxiliary lines stored and get ready to start over
     */
    init_auxlines() {
        this.aux_id = this.INIT_AUX_ID;
        this.aux_lines = {}
        this.aux_lines['global'] = []

        this.notify(this, PointModel.EVENT_INIT_AUXLINE, null);
    }

    /**
     * Clear all points stored and get ready to start over.
     */
    init_points(){
        this.points = {};
        this.point_id = this.INIT_PT_ID;

        let keys = this.get_output_properties();
        keys.push('ptid');
        keys.forEach((key) =>{
            this.points[key] = [];
        });

        // Keep the global aux lines (i.e. assume substance constant)
        let gl = this.aux_lines['global'];
        this.aux_lines = {};
        this.aux_lines['global'] = gl;

        this.notify(this, PointModel.EVENT_INIT_POINTS, null);
    }

    /**
     * Change the current units. This invalidates all stored point data.
     * @param units - a dict of the current units. Keys are unit category,
     *                    values are the unit value
     */
    set_units(units){
        this.units = units;
        // Reset everything
        this.init_auxlines();
        this.init_points();
        this.notify(this, PointModel.EVENT_UNIT, this.get_units())
    }

    /**
     * Change the current substance. This invalidates all stored point data
     * @param substance - a string for the substance. Must be in valid_substances.
     */
    set_substance(substance){
        if (!substance in this.valid_substances){
            throw new Error("Not a valid substance");
        }
        this.substance = substance;
        this.init_auxlines();
        this.init_points();
        this.notify(this, PointModel.EVENT_SUBSTANCE, this.get_substance())
    }

    /**
     * Get all valid units for PMGI
     * @returns valid_units - dict of valid units, keys are unit category,
     *                             values are arrays of legal values
     */
    get_valid_units(){
        if (this.valid_units != null) {
            return this.valid_units;
        } else {
            return [];
        }
    }

    /**
     * Get the current unit set
     * @returns units - a dict of the current units. Keys are unit category,
     *                  values are the unit value
     */
    get_units(){
        return this.units;
    }

    /**
     * Get the current unit strings for a list of properties
     * @returns units - a dict of the current units. Keys are property,
     *                  values are the unit value as a string
     */
    get_units_for_prop(props=[]){
        if (this.units === null) { return ""; }

        if (props.length === 0) {
            props = this.get_output_properties();
        }

        let unitstrs = {}
        props.forEach((prop) => {
            let propstr;
            // Case it out by the property
            if (prop === 'T') {
                propstr = this.units['temperature'];
            } else if (prop === 'p') {
                propstr = this.units['pressure'];
            } else if (prop === 'd') {
                propstr = this.units['matter'] + '/' + this.units['volume'];
            } else if (prop === 'v') {
                propstr = this.units['volume'] + '/' + this.units['matter'];
            } else if (prop === 'e' || prop === 'h') {
                propstr = this.units['energy'] + '/' + this.units['matter'];
            } else if (prop === 's' || prop === 'cp' || prop === 'cv') {
                propstr = this.units['energy'] + '/ (' + this.units['matter'] + ' ' + this.units['temperature'] + ')';
            } else {
                propstr = '-';
            }
            unitstrs[prop] = propstr;
        });
        if (props.length === 1) {
            return unitstrs[props[0]];
        } else {
            return unitstrs;
        }
    }

    /**
     * Get all valid substance data
     * @returns valid_substances - dict of valid substances, keys are the
     *                              substance id, values are a dict with info
     *                              from PMGI
     */
    get_valid_substances(){
        return this.valid_substances;
    }

    /**
     * Return the properties possible for the current substance
     * @returns {*} array of properties represented by strings
     */
    get_output_properties(){
        if (this.valid_substances != null && this.substance != null) {
            return [...this.valid_substances[this.substance]['props']]
        } else {
            return [];
        }
    }

    /**
     * Returns the input properties possible for the current substance
     * @returns {*} array of properties represented by strings
     */
    get_input_properties(){
        if (this.valid_substances != null && this.substance != null) {
            return this.valid_substances[this.substance]['inputs'];
        } else {
            return [];
        }
    }

    /**
     * Returns the current substance set
     * @returns substance - a string with the substance id.
     */
    get_substance(){
        return this.substance;
    }

    /**
     * Get all currently calculated points
     * @returns points - dict of arrays, where each array row is a single point.
     *                        dict is keyed by property name. Dict includes
     *                        an extra field ['ptid'] with a non-repeating
     *                        integer id for the points.
     */
    get_points(){
        return this.points;
    }


    /**
     * Get all currently computed aux iso lines
     * @returns lines - dict of arrays, key of parent dict is the parent of
     *                        the lines being reported ('global' for general
     *                        lines like the steamdome, etc.). The array values
     *                        of the dict contain two keys: 'type' and 'data'.
     *                        The string 'type' represents the property
     *                        associated with this particular line (e.g. 'p'
     *                        for an isobar. 'data' is a dict, keyed by
     *                        property name and whose values are arrays of
     *                        values making up the whole line.
     *
     *                        lines['global'][0]['data']['p'] gets the pressure
     *                        values for a given line in global at index 0.
     */
    get_auxlines(id=null){
        if (id == null) {
            return this.aux_lines;
        } else if (id in this.aux_lines){
            return {id: this.aux_lines[id]};
        }
    }

    /**
     * Add a new point to the list
     * @param point - A dict keyed by property. An integer ID will be added to
     *                  the point for internal tracking.
     */
    add_point(point){
        let pt = Object.assign({}, point);  // Copy object
        pt['ptid'] = this.point_id;  // Append the id to the point

        // Push to the existing array
        for (const key in pt) {
            this.points[key].push(pt[key]);
        }
        // Increment the id and notify
        this.point_id++;
        this.notify(this, PointModel.EVENT_POINT_ADD, pt);
    }

    /**
     * Remove a point based on its integer id
     * @param id - the integer id of the point (via 'ptid' property)
     */
    delete_point(id){
        // Points is a dict keyed by property, with arrays
        let index = this.points['ptid'].indexOf(parseInt(id));
        for (const key in this.points) {
            this.points[key].splice(index, 1);
        }
        this.delete_auxlines(id);

        // If this was the last point, we want to clear things out.
        if (this.points['ptid'].length === 0){
            this.init_points();
        } else {
            this.notify(this, PointModel.EVENT_POINT_DELETE, id);
        }
    }

    /**
     * Add a new auxiliary line
     * @param type - string, iso-property
     * @param data - dict of property value arrays
     * @param parent - ptid of parent point being represented, or 'global'
     */
    add_auxline(type, data, parent='global'){
        // If it's a new parent, the array might not exist yet, initialize
        if (!(parent in this.aux_lines)){
            this.aux_lines[parent] = [];
        }
        let line = {'type': type, 'id': this.aux_id, 'data': data};
        this.aux_id++;
        this.aux_lines[parent].push(line);
        this.notify(this, PointModel.EVENT_AUXLINE_ADD, line);
    }

    /**
     * * Remove an auxiliary line its parent point integer id
     * @param id - the integer id of the parent point (via 'ptid' property)
     */
    delete_auxlines(id){
        // Make sure we've computed auxlines for this point first
        if (id in this.aux_lines){
            delete this.aux_lines[id];
            this.notify(this, PointModel.EVENT_AUXLINE_DELETE, id);
        }
    }
}

// *********************************************
// * VIEWS
// *********************************************

/**
 * Class to handle the substance selector. Data stored in PointModel
 */
class SubstanceFormView{

    constructor(formHTMLid, show_all=false) {
        this.select_name = "select";

        this.show_all = show_all;
        this.target = $("#"+formHTMLid);
        let select = $('<select/>').attr({id: this.select_name});
        this.target.append(select);
        this.select = $('#'+this.select_name, this.target);
    }

    update(source, event, data){
        if (event === PointModel.EVENT_SUBSTANCE){
            this.set_value(data);  // Set the current value to the model's state
        }
    }

    /**
     * Set the value the selector should take
     * @param substance - A substance id as a string
     */
    set_value(substance){
        this.select.val(substance);
    }

    /**
     * Create the substance selector
     * @param substances - All possible substances, expected as dictionary with
     *                      keys of the substance id that will appear in the list.
     * @param current_value - The id of the value you want the selector to have
     * @param shortlist - A shortlist array of substance_ids to display in the list
     */
    init(substances, current_value=null, shortlist=null){

        let subsel = this.select;
        // Loop over the substances, create option group for each category
        Object.keys(substances).forEach(subst => {
            if (this.show_all || shortlist == null || shortlist.includes(subst)) {
                subsel.append($("<option>").val(subst).text(subst));
            }
        });

        // The event handler for changes, which provides a confirmation.
        subsel.on("change", ()=>{
            let success = confirm('Changing the substance will reset all data. Are you sure?');
            if(success){
                // Call the set_substance method of the controller.
                set_substance(subsel.val());
            } else {
                // undo
                this.set_value(get_substance());
                return false;
            }
        });

        if (current_value !== null) {
            this.set_value(current_value);
        }
    }
}

/**
 * A class for controlling the form that allows the user to specify units.
 * Data stored in PointModel
 */
class UnitFormView{

    constructor(formHTMLid) {
        this.target = $("#"+formHTMLid);
        this.button_hide_name = "unit_hide";
        this.unit_list_div_name = "hideablelist";
        this.unit_form_name = "unitform";
        this.button_apply_name = "unit_apply";
        this.button_revert_name = "unit_revert";

        // Create the hide button and assign its callback.
        let hidebutton = $('<input/>').attr({type: 'button', id: this.button_hide_name, value: "Units"});
        this.target.append(hidebutton);
        this.button_hide = $('#'+this.button_hide_name, this.target);
        this.hide_onclick = this.hide_onclick.bind(this);
        this.button_hide.on("click", this.hide_onclick);


        // Create a <ul> to hold the checklist, and the checklist
        let unitlist = $('<ul/>').attr({id: this.unit_list_div_name, style: "display: none"});
        this.target.append(unitlist);
        this.unit_list_div = $('#'+this.unit_list_div_name, this.target);
        let unitform = $('<form/>').attr({id: this.unit_form_name});
        this.unit_list_div.append(unitform);
        this.unit_form = $('#'+this.unit_form_name, this.target);

        // Create the apply and revert buttons
        let applybutton = $('<input/>').attr({type: 'button', id: this.button_apply_name, value: "Apply", style: "display: none"});
        this.unit_list_div.append(applybutton);
        this.button_apply = $('#'+this.button_apply_name, this.target);
        this.apply_onclick = this.apply_onclick.bind(this);
        this.button_apply.on("click", this.apply_onclick);

        let revertbutton = $('<input/>').attr({type: 'button', id: this.button_revert_name, value: "Revert", style: "display: none"});
        this.unit_list_div.append(revertbutton);
        this.button_revert = $('#'+this.button_revert_name, this.target);
        this.revert_onclick = this.revert_onclick.bind(this);
        this.button_revert.on("click", this.revert_onclick);
    }


    update(source, event, data){
        if (event === PointModel.EVENT_UNIT){
            this.set_values(data);
        }
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

            $select.on("change", ()=>{
                this.button_apply.show();
                this.button_revert.show();
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
            this.button_apply.hide();
            this.button_revert.hide();
            set_units(this.get_values())
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
        this.set_values(get_units());
        this.button_apply.hide();
        this.button_revert.hide();
    }

    /**
     * User clicks the show/hide button
     */
    hide_onclick(){
        this.unit_list_div.toggle();
    }
}

/**
 * A class for managing the form that consists of property data entry
 */
class PropEntryView{
    constructor(formHTMLid) {
        this.target = $("#"+formHTMLid);
        this.prop_table_name = "propinput";
        this.prop_form_name = "propform";
        this.post_button_name = "post_props";

        let propform = $('<form/>').attr({id: this.prop_form_name});
        this.target.append(propform);
        this.prop_form = $("#"+this.prop_form_name, this.target);

        let proptable = $('<table/>').attr({id: this.prop_table_name});
        this.target.append(proptable);
        this.prop_table = $("#"+this.prop_table_name, this.target);

        let postbutton = $('<input/>').attr({type: 'button', id: this.post_button_name, value: "Compute"});
        this.target.append(postbutton);
        this.post_button = $("#"+this.post_button_name, this.target);
        this.post_onclick = this.post_onclick.bind(this);
        this.post_button.on("click", this.post_onclick);
    }

    update(source, event, data){
        if (event === PointModel.EVENT_SUBSTANCE) {
            let prop_vals = this.get_values();  // Retain values
            this.init(get_input_properties(), get_unit_strings(), prop_vals);
        } else if (event === PointModel.EVENT_UNIT) {
            this.init(get_input_properties(), get_unit_strings());
        }
    }

    /**
     * Initialize things
     * @param input_properties - An array of input property strings
     * @param unit_strings - A dict of units keyed by prop
     * @param prop_values - a dict keyed by property and with string values
     */
    init(input_properties, unit_strings=null, prop_values=null) {
        this.create_propform(input_properties, unit_strings);
        this.set_form_values(prop_values);
    }

    /**
     * Build the form. Note that an extra HTML attribute of propvalue will be
     * used to specify the actual property string separate from the name.
     * @param props - an array of property strings
     * @param units - an dict of unit strings by prop
     */
    create_propform(props, units=null) {
        // Always start from scratch
        this.prop_table.empty();

        // Build a header
        let head = "<thead><tr>"
        props.forEach((prop) => {
            if (units != null){
                prop = prop + " (" + units[prop] +")";
            }
            head = head + "<th>" + prop + "</th>";
        });
        head = head + "</tr></thead>";

        this.prop_table.append(head);

        // Build each input box
        let tr = $("<tr>")
        props.forEach((prop) => {
            let td = $("<td>");
            // Use string formatting to prevent insanity
            let inputbox = `<input type="text" propvalue="${prop}" id="${prop}_input" name="${prop}_input">`;
            tr.append(td.append(inputbox));
        });
        this.prop_table.append(tr);
    }

    /**
     * Copy existing values into the boxes
     * @param props - a dict keyed by property and with string values
     */
    set_form_values(props) {
        if (props != null) {
            $('input', this.prop_table).each((id, box) => {
                let boxkey = box.attributes['propvalue'].nodeValue;
                if (Object.keys(props).includes(boxkey)) {
                    box.value = props[boxkey];
                }
            });
        }
    }

    /**
     * Convert the form values to a dict of output data
     * @returns data - a dict keyed by property and string vals
     */
    get_values() {
        let outdata = {}; // A dict of specified props

        // Loop over each input box
        $('input', this.prop_table).each((id, box) =>{
            let value = box.value;
            if (value !== ""){ // If specified, add it to the prop dict
                let prop = box.attributes['propvalue'].nodeValue;
                outdata[prop] = value;
            }
        });
        return outdata;
    }

    /**
     * A callback to execute computing a point based on the form data.
     */
    post_onclick(){
        compute_point(this.get_values(), "POST");
    }

}

/**
 * A class for managing the form that allows a user to specify which properties
 * to show.
 * Data stored by this object, technically not just a View?
 */
class PropChooserView extends Subject{
    static EVENT_PROPERTY_VISIBILITY = 'propvis'; // When the checkboxes change
    static EVENT_ISOLINE_VISIBILITY = 'isolinevis'; // When the checkboxes change
    constructor(target_div_id, event_type, shortlist = null) {
        super();
        this.event_type = event_type;
        this.shortlist = shortlist;

        this.target_name = target_div_id;
        this.hide_checks_name = "propchoice_hide";
        this.prop_checks_name = "propchecks";

        // Initialize selectors for the components that make up this control
        this.target = $("#" + this.target_name);

        // Create the show/hide button
        let hidebutton = $('<input/>').attr({type: 'button', id: this.hide_checks_name, value: "Show Props"});
        this.target.append(hidebutton);
        // Get its selector
        this.hide_checks = $('#'+this.hide_checks_name, this.target);

        // Create a <ul> to hold the checklist
        let checklist = $('<ul/>').attr({id: this.prop_checks_name, style: "display: none"});
        this.target.append(checklist);
        // Get its selector
        this.prop_checks = $('#'+this.prop_checks_name, this.target);

        this.hide_checks.on("click", () =>{
            this.prop_checks.toggle();  // Toggle visibility of checklist
        });

        // Since these will be used as callbacks, they need to be bound
        this.checkbox_onchange = this.checkbox_onchange.bind(this);
    }


    update(source, event, data) {
        if (event === PointModel.EVENT_SUBSTANCE) {
            let disp_props = this.get_checkbox_values();
            this.init(source.get_output_properties(), disp_props);
        }
    }

    /**
     * Initialize
     * @param valid_properties - an array of valid property strings
     * @param show_properties - an array of properties that are true
     */
    init(valid_properties, show_properties) {
        this.create_checkboxes(valid_properties);
        this.set_checkbox_values(show_properties);

        this.notify(this, this.event_type, this.get_checkbox_values());
    }

    /**
     * Build the checkboxes
     * @param valid_properties - an array of valid property strings
     */
    create_checkboxes(valid_properties) {
        this.prop_checks.empty();
        // Loop over all properties
        valid_properties.forEach(prop => {
            if (this.shortlist == null || this.shortlist.includes(prop)) {
                // The form will be a list of labelled check boxes
                let $li = $("<li>")
                let $label = $('<label>' + prop + '</label>', {});

                // Add this checkbox
                let $checkbox = $('<input>', {
                    type: "checkbox",
                    value: prop,
                    id: prop + '_box',
                    name: prop + '_box'
                });

                // add the callback
                $checkbox.on("click", this.checkbox_onchange);

                // Add the objects to the form
                this.prop_checks.append($li.append($label).append($checkbox));
            }
        });
    }

    /**
     * Callback for when one of the checkboxes is changed
     */
    checkbox_onchange(){
        let disp_props = this.get_checkbox_values();
        this.notify(this, this.event_type, disp_props);
    }

    /**
     * Get the values of the checkboxes
     * @returns names - an array of property strings that are checked
     */
    get_checkbox_values() {
        let names = [];
        $('input:checked', this.prop_checks).each((id, box) => {
            names.push(box.value);
        });
        return names;
    }

    /**
     * Set the values of the checkboxes
     * @param show_properties - an array of property strings that should be checked
     */
    set_checkbox_values(show_properties) {

        $('input', this.prop_checks).each((id, box) => {
            let prop = box.value;
            let checked = show_properties.includes(prop);
            if (checked) {
                box.checked = true;
            } else {
                box.checked = false;
            }
        });
    }


    // ******** Legacy code for disabling boxes to control inputs. Keep?
    //
    // function updateinputs() {
    //     // First, count the number of nonzero entries
    //     var count;
    //     var inputs = [document.getElementById("Tinput"), document.getElementById("pinput"), document.getElementById("dinput"), document.getElementById("hinput"), document.getElementById("sinput")];
    //     var x;
    //
    //     count = 0;
    //     for (x of inputs){
    //         if (x.value.length){
    //             count += 1;
    //         }
    //     }
    //
    //     if(count < 2){
    //         for (x of inputs){
    //             x.disabled = false;
    //         }
    //     }else{
    //         for (x of inputs){
    //             if (x.value.length==0){
    //                 x.disabled = true;
    //             }
    //         }
    //     }
    //
    //     // Then, grey out the entries that are zero (if appropriate)
    // }
}


/**
 * A helper for dealing with the plot positions. In number between min & max?
 */
Number.prototype.between = function(min, max) {
    return this >= min && this <= max;
};

/**
 * A plot of the data
 */
class PlotView{
    TRACEORDER = ['user','steamdome','p','T','d', 'h', 's', 'x']
    TRACENAMES = ['User Data', 'Steam Dome', 'Const. p', 'Const. T', 'Const. d', 'Const. h', 'Const. s', 'Const. x']
    TRACECOLORS = ['']

    constructor(divTarget) {
        // TODO - plot prettiness
        this.dispprops = ['T','s','p','v'];
        this.dispisos = ['T', 'p', 'h'];
        this.target = $("#"+divTarget);
        this.plot_div_name = "plot";

        this.create_axis_selects();

        // Create the div for the plot
        let plot = $("<div/>").attr({id: this.plot_div_name});
        this.target.append(plot);
        this.plot = $("#"+this.plot_div_name, this.target);

        this.traces = [];

        this.init();
    }

    create_axis_selects(){
        // Create the axis selector Buttons
        let xaxis_defs = {id: 'xprop', def: 's', opts: ['T','v','h','s'], label: 'X Property'};
        let yaxis_defs = {id: 'yprop', def: 'T', opts: ['T','p'], label: 'Y Property'};

        this.onChangeAxes = this.onChangeAxes.bind(this);

        // Create a div to put the buttons within
        let btnholder = $("<div/>").attr({id: "buttons"});
        [xaxis_defs, yaxis_defs].forEach((defaults)=>{
            let label = $("<label>").text(defaults['label']).attr({labelfor: defaults['id']});
            btnholder.append(label);

            let sel = $("<select/>").attr({id: defaults['id'], name: defaults['id'], value: defaults['def']});
            defaults['opts'].forEach((opt) =>{
               let newopt = $("<option>").val(opt).text(opt);
               sel.append(newopt);
            });
            sel.val(defaults['def']).change();
            sel.on("change", this.onChangeAxes)
            btnholder.append(sel);
        });
        this.target.append(btnholder);

        // Set the button callbacks
        this.xprop_sel = $("#"+xaxis_defs['id'], this.target);
        this.yprop_sel = $("#"+yaxis_defs['id'], this.target);
        this.setAxes(this.xprop_sel.val(), this.yprop_sel.val());
    }

    init(){
        this.set_layout();
        // Create the plot trace
        this.traces = [];
        this.traces.push({
            x: [],
            y: [],
            customdata: [],
            mode: 'markers',
            name: "User Points",
            hovertemplate: "<b> Point prop</b><br>"+
                this.x_prop+": %{x}<br>" +
                this.y_prop+": %{y}<br>" +
                "attr: %{customdata}",
            type: 'scatter'
        });
        this.traces.push({
            x: [],
            y: [],
            mode: 'lines',
            type: 'scatter',
            name: 'Steam Dome',
            hovertemplate: " ",
            showlegend: false,
            line: {
                color: 'rgb(0, 0, 0)',
                width: 3
            }
        });
        this.traces.push({
            x: [],
            y: [],
            mode: 'lines',
            type: 'scatter',
            name: 'isolines p',
            hovertemplate: "<b>Isobar</b><br>"+
                "p: %{customdata:.5g}",
            showlegend: false,
            line: {
                color: 'rgb(0, 100, 0)',
                width: 1
            }
        });
        this.traces.push({
            x: [],
            y: [],
            mode: 'lines',
            type: 'scatter',
            name: 'isolines p',
            hovertemplate: "<b>Isotherm</b><br>"+
                "T: %{customdata:#.4g}",
            showlegend: false,
            line: {
                color: 'rgb(155, 0, 0)',
                width: 1
            }
        });
        this.traces.push({
            x: [],
            y: [],
            mode: 'lines',
            type: 'scatter',
            name: 'isolines d',
            hovertemplate: "<b>Iso-d Line</b><br>"+
                "d: %{customdata:#.4g}",
            showlegend: false,
            line: {
                color: 'rgb(0, 155, 155)',
                width: 1
            }
        });
        this.traces.push({
            x: [],
            y: [],
            mode: 'lines',
            type: 'scatter',
            name: 'isolines h',
            hovertemplate: "<b>Iso-h Line</b><br>"+
                "h: %{customdata:#.4g}",
            showlegend: false,
            line: {
                color: 'rgb(155, 155, 0)',
                width: 1
            }
        });
        this.traces.push({
            x: [],
            y: [],
            mode: 'lines',
            type: 'scatter',
            name: 'isolines s',
            hovertemplate: "<b>Iso-s line</b><br>"+
                "s: %{customdata:#.3g}",
            showlegend: false,
            line: {
                color: 'rgb(0, 0, 155)',
                width: 1
            }
        });
        this.traces.push({
            x: [],
            y: [],
            mode: 'lines',
            type: 'scatter',
            name: 'isolines x',
            hovertemplate: "<b>Iso-x line</b><br>"+
                "x: %{customdata:#.2g}",
            showlegend: false,
            line: {
                color: 'rgb(155, 0, 155)',
                width: 1
            }
        });
        // Create the plot object
        Plotly.newPlot(this.plot.get()[0], this.traces, this.layout);
        this.setupPlotClickListener();
    }

    /**
     * Details for styling the plot
     */
    set_layout(){
        let x_scale;
        let y_scale;
        if (this.x_prop === 'v' || this.x_prop === 'p'){
            x_scale = 'log';
        } else {
            x_scale = 'linear';
        }
        if (this.y_prop === 'p'){
            y_scale = 'log';
        } else {
            y_scale = 'linear';
        }

        this.layout = {
            xaxis: {
                title: this.x_prop + " (" + get_unit_strings([this.x_prop])+")",
                type: x_scale,
                autorange: true
            },
            yaxis: {
                title: this.y_prop + " (" + get_unit_strings([this.y_prop])+")",
                type: y_scale,
                autorange: true
            },
            margin: { t: 0 }
        };
    }

    /**
     * A listener for dealing with the user clicking to add a point
     */
    setupPlotClickListener(){
        let myPlot = this.plot.get()[0];
        let myPlotContainer = this;
        d3.select(".plotly").on('click', function(d, i) {
            let e = d3.event;
            let bgrect = document.getElementsByClassName('gridlayer')[0].getBoundingClientRect();
            let x = 0;
            let y = 0;
            let betweenx = false;
            let betweeny = false;
            // X Axis
            if (myPlotContainer.layout['xaxis']['type'] === 'linear') {
                x = ((e.x - bgrect['x']) / (bgrect['width'])) * (myPlot.layout.xaxis.range[1] - myPlot.layout.xaxis.range[0]) + myPlot.layout.xaxis.range[0];
                betweenx = x.between(myPlot.layout.xaxis.range[0], myPlot.layout.xaxis.range[1]);
            } else if (myPlotContainer.layout['xaxis']['type'] === 'log'){
                x = 10**(((e.x - bgrect['x']) / (bgrect['width'])) * (myPlot.layout.xaxis.range[1] - myPlot.layout.xaxis.range[0]) + myPlot.layout.xaxis.range[0]);
                betweenx = Math.log10(x).between(myPlot.layout.xaxis.range[0], myPlot.layout.xaxis.range[1]);
            }
            // Y Axis (flipped coords)
            if (myPlotContainer.layout['yaxis']['type'] === 'linear') {
                y = ((e.y - bgrect['y']) / (bgrect['height'])) * (myPlot.layout.yaxis.range[0] - myPlot.layout.yaxis.range[1]) + myPlot.layout.yaxis.range[1];
                betweeny = y.between(myPlot.layout.yaxis.range[0], myPlot.layout.yaxis.range[1]);
            } else if (myPlotContainer.layout['yaxis']['type'] === 'log') {
                y = 10 ** (((e.y - bgrect['y']) / (bgrect['height'])) * (myPlot.layout.yaxis.range[0] - myPlot.layout.yaxis.range[1]) + myPlot.layout.yaxis.range[1]);
                betweeny = Math.log10(y).between(myPlot.layout.yaxis.range[0], myPlot.layout.yaxis.range[1]);
            }

            if (betweenx && betweeny) {
                // Build the data and send to the controller
                let formData = {}
                formData[myPlotContainer.x_prop] = x
                formData[myPlotContainer.y_prop] = y
                compute_point(formData, "POST");
            }
        });
    }

    update(source, event, data){
        if (event === PointModel.EVENT_POINT_ADD || event === PointModel.EVENT_POINT_DELETE){
            this.updatePoints(source.get_points());
        } else if (event === PointModel.EVENT_INIT_POINTS || event === PointModel.EVENT_UNIT) {
            this.init();
            this.draw_auxlines(source.get_auxlines());
        } else if (event === PropChooserView.EVENT_PROPERTY_VISIBILITY) {
            this.dispprops = data;
            this.updatePoints(get_points());
        } else if (event === PropChooserView.EVENT_ISOLINE_VISIBILITY){
            this.dispisos = data;
            this.draw_auxlines(get_auxlines());
        } else if (event === PointModel.EVENT_AUXLINE_ADD) {
            this.draw_auxlines(source.get_auxlines());
        }
    }


    onChangeAxes(){
        this.setAxes(this.xprop_sel.val(), this.yprop_sel.val())
        this.init();
        this.draw_auxlines(get_auxlines());
        this.updatePoints(get_points());
    }

    setAxes(xprop, yprop){
        this.x_prop = xprop;
        this.y_prop = yprop;
    }


    /**
     * Handle updates to the auxiliary lines on the plot (i.e. isobars, dome)
     * @param data - the isolines dict corresponding to PointModel.get_auxlines()
     */
    draw_auxlines(data){
        // Loop over every iso-trace that we put in the diagram
        this.TRACEORDER.forEach((prop) =>{

            // Establish the index in the order of the traces
            let ind = this.TRACEORDER.indexOf(prop);
            if (ind > 0) { // ind 0 is the user points

                // Make a placeholder for the updates
                let iso_update = null;

                if (prop === 'steamdome' ||
                    (this.x_prop !== prop && this.y_prop !== prop &&
                        this.dispisos.includes(prop))
                ) {
                    // Loop over all the aux lines that are in the "global" category
                    data['global'].forEach((line) => {

                        if (line['type'] === prop) {

                            // Initialize the trace update on the first call
                            if (iso_update == null) {
                                iso_update = {};
                                Object.keys(line['data']).forEach((key) => {
                                    iso_update[key] = [];
                                });
                            }

                            // Add the line to the trace property by property
                            Object.keys(line['data']).forEach((key) => {
                                iso_update[key] = iso_update[key].concat(line['data'][key]);
                                iso_update[key].push(null);
                            });
                        }
                    });
                }

                // Send the updated traces to the actual plot
                let update = {
                        x: [null],
                        y: [null],
                        customdata: [null]  // Display their text
                    };
                if (iso_update != null) {
                    update = {
                        x: [iso_update[this.x_prop]],
                        y: [iso_update[this.y_prop]],
                        customdata: [iso_update[prop]]  // Display their text
                    };
                }
                Plotly.restyle(this.plot.get()[0], update, [ind]);
            }
        });
    }

    /**
     * Handling points being added to the list of points
     * @param points
     */
    updatePoints(points) {
        // Build the customdata object for the tooltip according to the API
        // Object takes the form [[h1,v1,s1,...],[h2,v2,s2,...],[h3,v3,s3,...]]

        // Loop over all the points
        let allkeys = Object.keys(points);
        if (allkeys.length >0) {  // Only if there are points
            let customdataset = [];  // The custom data that will be added to the tooltip
            let keylist = [];
            for (let i = 0; i < points['ptid'].length; i++) {  // Loop over all points
                let arr = [] // Build an array of all props for this index.
                arr.push(points['ptid'][i]); // Make the index the very first datapoint.

                allkeys.forEach(key => {
                    if (key !== this.x_prop &&
                        key !== this.y_prop &&
                        this.dispprops.includes(key)) {
                        if (i === 0) {
                            keylist.push(key);
                        }
                        arr.push(points[key][i]);
                    }
                });
                customdataset.push(arr);
            }

            // customdataset is now ordered as (ptid, T, p, v, ...)

            // Build the strings that represent the tooltip
            let customrows = "";
            for (let i = 0; i < keylist.length; i++) {
                customrows = customrows + keylist[i] + ": %{customdata[" + (i + 1) + "]:#.5g}<br>";
            }

            // Fully replace User Point trace, including the custom data
            let update = {
                x: [points[this.x_prop]],
                y: [points[this.y_prop]],
                customdata: [customdataset],
                hovertemplate: "<b>Point %{customdata[0]}</b><br>" +
                    this.x_prop + ": %{x}<br>" +
                    this.y_prop + ": %{y}<br>" +
                    customrows,
            }

            let ind = this.TRACEORDER.indexOf('user');
            Plotly.restyle(this.plot.get()[0], update, [ind])
        }
    }
}

/**
 * A class for managing the interactive table
 */
class TableView{
    // delete rows? https://stackoverflow.com/questions/64526856/how-to-add-edit-delete-buttons-in-each-row-of-datatable
    // showhide columns https://datatables.net/examples/api/show_hide.html
    constructor(divTarget) {
        this.target = $("#"+divTarget);

        // create a <table> within the div that we'll operate on
        this.tabletarget = $("<table id='proptable'></table>");
        this.target.append(this.tabletarget);

        this.proptext_to_id = {};
        this.table = null
    }

    init(props){
        this.dispprops = [...props]; // copy of props
        if (!this.dispprops.includes('ptid')){
            this.dispprops.unshift("ptid");// ptid should be in the table but not the prop list
        }

        if (this.table == null){
            this.tabletarget.empty();
            let $head = $('<thead></thead>');
            let $foot = $('<tfoot></tfoot>'); // Havent figured out the footer
            let $r = $('<tr></tr>')
            this.proptext_to_id = {};
            this.dispprops.forEach((prop) =>{
                let propstr = prop;
                if (prop !== 'ptid'){
                    propstr = propstr + " ("+get_unit_strings([prop])+")";
                    this.proptext_to_id[propstr] = prop;
                }
                let $th = $('<th>'+propstr+'</th>');
                $r.append($th);
            });
            $r.append('<th>Ctrl</th>');
            $head.append($r);
            //$foot.append($r);
            this.tabletarget.append($head);
            //$tablediv.append($foot);


            // Build the data table with null content. Insert the delete button in the extra column.
            let table = new DataTable(this.tabletarget, {
                "columnDefs": [ {
                    "targets": -1,
                    "data": null,
                    "defaultContent": "<button id='click2del'>Delete</button>"
                } ]
            });

            // Click handler for each row's delete button
            $('tbody', this.tabletarget).on( 'click', 'button', function () {
                let data = table.row( $(this).parents('tr') ).data();
                delete_point(data[0]);
            } );
            this.table = table;
        } else {
            this.table.destroy();
            this.table = null;
            this.init(props);
        }

        // Redraw
        this.table.clear().draw();
    }

    update(source, event, data){
        if (event === PointModel.EVENT_POINT_ADD || event === PointModel.EVENT_POINT_DELETE){
            this.updatePoints(source.get_points());
        } else if (event === PointModel.EVENT_INIT_POINTS) {
            this.init(get_output_properties());
        } else if (event === PropChooserView.EVENT_PROPERTY_VISIBILITY) {
            this.columnVisibility(data);
        }
    }

    /**
     * Change visibility of columns
     * @param columns - an array of property names to display
     */
    columnVisibility(columns){

        this.table.columns().every((ind) => {
            let col = this.table.column(ind);
            let name = col.header().textContent
            // Always display ptid and ctrl columns
            if (name==="ptid" || name==="Ctrl" || columns.includes(this.proptext_to_id[name]) ){
                col.visible(true);
            } else {
                col.visible(false);
            }
        });

    }

    /**
     * The points changed, redraw the table
     * @param points - All the points. Dict keyed by property, valued by array
     *                  of individual point values.
     */
    updatePoints(points) {

        // Clear them all
        this.table.rows().remove();

        let customdataset = [];
        for (let i=0; i<points['ptid'].length; i++ ){  // Loop over all points
            let arr = [] // Build an array of all props for this index.
            //arr.push(points['ptid'][i]); // Now included in points.
            // Loop over all props, add if exists
            this.dispprops.forEach(key => {
                if (key in points) {
                    arr.push(points[key][i].toLocaleString('en-US', {
                        maximumSignificantDigits: 5
                    }));
                }
            });
            customdataset.push(arr)
        }

        for (let i=0; i<customdataset.length; i++ ) {  // Loop over all rows
            this.table.row.add(customdataset[i]).draw(); // add to table
        }
    }
}


// *********************************************
// * CONTROLLER
// *********************************************

// Define the classes
var unitFormView;
var substanceFormView;
var propChooserView;
var isolineChooserView;
var propEntryView;
var plotView;
var tableView;
var pointModel;


// Execute when the page loads
$(document).ready(function(){
    // Instantiate classes with their targets
    pointModel = new PointModel();
    unitFormView = new UnitFormView('unit_controls');
    substanceFormView = new SubstanceFormView('substance_controls');
    propChooserView = new PropChooserView("property_selection", PropChooserView.EVENT_PROPERTY_VISIBILITY);
    isolineChooserView = new PropChooserView("isoline_selection", PropChooserView.EVENT_ISOLINE_VISIBILITY, ['T','d','p','s','h','x']);
    propEntryView = new PropEntryView("property_controls");
    tableView = new TableView('property_table');
    plotView = new PlotView("plot_display");

    // getInfo is an async request, so use the callback to complete setup.
    getInfo((data)=>{
        // Get the general info data, assign to model
        pointModel.init_info(data.valid_units, data.substances);
        set_units(data.units);
        set_substance(pointModel.DEFAULT_SUBSTANCE);

        // Assign views to listen to the main model
        pointModel.addListener(unitFormView);
        pointModel.addListener(substanceFormView);
        pointModel.addListener(tableView);
        pointModel.addListener(plotView);
        pointModel.addListener(propChooserView);
        pointModel.addListener(isolineChooserView);
        pointModel.addListener(propEntryView);

        // Assign views to listen to the views that hold state data
        propChooserView.addListener(tableView);
        propChooserView.addListener(plotView);

        isolineChooserView.addListener(plotView);

        // Call inits on views now that the properties exist
        tableView.init(get_output_properties());
        plotView.init();
        unitFormView.init(get_valid_units(), get_units());
        substanceFormView.init(get_valid_substances(), get_substance(), get_display_substances());
        propChooserView.init(get_output_properties(), pointModel.DEFAULT_PROP_SHORTLIST);
        isolineChooserView.init(get_output_properties(), ['T','p','x']);
        propEntryView.init(get_input_properties(), get_unit_strings());
    });
});


// Passthrough controller functions that get/set on behalf of the model

function get_output_properties(){
    // TODO - consider where this belongs
    return pointModel.get_output_properties();
}

function get_input_properties(){
    return pointModel.get_input_properties();
}

function get_display_substances(){
    return pointModel.DEFAULT_SUB_SHORTLIST;
}

function get_valid_units(){
    return pointModel.get_valid_units();
}

function get_valid_substances(){
    return pointModel.get_valid_substances();
}

function get_points(){
    return pointModel.get_points();
}

function add_point(point){
    pointModel.add_point(point);
}

function delete_point(point){
    pointModel.delete_point(point)
}

function get_auxlines(){
    return pointModel.get_auxlines();
}

function set_substance(newsubstance){
    pointModel.set_substance(newsubstance);
    calc_auxline();
}

function calc_auxline(){
    if (get_substance().startsWith('mp')){
        compute_auxline((data)=>{
            let sll = data.data['liquid'];
            let svl = data.data['vapor'];
            // concatenate vapor to liquid
            Object.keys(svl).forEach(key => {
                for (let i = svl[key].length; i > -1; i--) {
                    sll[key].push(svl[key][i]);
                }
            });
            add_steamdome(sll);
        });

        compute_auxline((data)=>{
            data.data.forEach((line)=>{
                pointModel.add_auxline('x', line, 'global');
            });
        },{'x': 0, 'default': true});
    }

    // Add a few types of lines
    ['p', 'T', 'd', 'h', 's'].forEach((prop_val)=>{
        compute_args = {};
        compute_args[prop_val] = 0;
        compute_args["default"] = true;
        compute_auxline((data)=>{
            data.data.forEach((line)=>{
                pointModel.add_auxline(prop_val, line, 'global');
            });
        },compute_args);
    })
}

function add_steamdome(steamdome){
    pointModel.add_auxline('steamdome', steamdome, parent='global');
}

function get_substance(){
    return pointModel.get_substance();
}

function get_units(){
    return pointModel.get_units();
}

function get_unit_strings(props=[]){
    return pointModel.get_units_for_prop(props);
}

function set_units(units){
    pointModel.set_units(units);
    if (get_substance() != null){
        calc_auxline();
    }
}

// *********************************************
// * CONTROLLER - AJAX
// *********************************************


/**
 * Async request for getting a state from the backend.
 * @param props - Dict with keys of property and numeric values
 * @param mode - GET/POST. Only POST can handle units with the request
 */
function compute_point(props, mode="POST"){
    let requestroute = "/";

    // Add the substance ID to props always
    props['id'] = get_substance();

    // TODO - Callbacks are hardcoded, keep or lose?
    if (mode === "GET"){
        $.get(requestroute, props, propResponseSuccess,dataType='json')
            .fail(propResponseFail);
    } else if (mode === "POST") {
        let postData = {state_input: props, units: get_units()};
        $.ajax({
            url: requestroute,
            type: "POST",
            data: JSON.stringify(postData),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            success: propResponseSuccess,
            error: propResponseFail
        });
    }
}

/**
 * Async request for getting a state from the backend.
 * @param callback - function handle to execute when complete
 * @param props - Dict with keys of property and numeric values
 * @param mode - GET/POST. Only POST can handle units with the request
 */
function compute_auxline(callback, props={}, mode="POST"){
    let requestroute;
    if (Object.keys(props).length === 0) {
        requestroute = "/saturation";
    } else {
        requestroute = "/isoline"
    }

    // Add the substance ID to props always
    props['id'] = get_substance();

    if (mode === "GET"){
        $.get(requestroute, props, callback,dataType='json')
            .fail(propResponseFail);
    } else if (mode === "POST") {
        let postData = {state_input: props, units: get_units()};
        $.ajax({
            url: requestroute,
            type: "POST",
            data: JSON.stringify(postData),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            success: callback,
            error: propResponseFail
        });
    }
}

/**
 * Async request to get global info
 * @param callback - a function handle for the response success
 */
function getInfo(callback){
    // Get all the PM info.
    $.get("/info",
        callback,
        dataType='json')  // Data type of the response.
        .fail(propResponseFail);  // What to do if it doesn't work
}

/**
 * Callback for when a point data request completes
 * @param data - JSON data from the flask backend
 */
function propResponseSuccess(data){
    add_point(data.data);
}

/**
 * Callback for when a flask request fails
 * @param data
 */
function propResponseFail(data){
    // TODO better error handling?
    try {
        let resp = JSON.parse(data.responseText);
        alert(resp.message);
    } catch (error) {
        alert("An unhandled error occurred: " + data.responseText);
    }
}





