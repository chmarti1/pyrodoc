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
    static EVENT_POINT = 'point' // Data will be get_points()
    static EVENT_INIT = 'init'; // Data will be null

    DEFAULT_SUB_SHORTLIST=["mp.H2O","mp.C2H2F4","ig.air","ig.O2", "ig.N2"];
    DEFAULT_PROP_SHORTLIST=["T","p","v","e","h","s","x"];
    DEFAULT_SUBSTANCE = 'mp.H2O'
    INIT_ID = 1

    constructor() {
        super();
        // Current list of defined points
        this.points = []
        this.point_id = this.INIT_ID;

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
    init(valid_units, valid_substances){
        this.valid_units = valid_units;
        this.valid_substances = valid_substances;
    }

    /**
     * Change the current units. This invalidates all stored point data.
     * @param units - a dict of the current units. Keys are unit category,
     *                    values are the unit value
     */
    set_units(units){
        this.units = units;
        this.clearpoints();
        this.notify(this, PointModel.EVENT_UNIT, this.get_units())
    }

    /**
     * Change the current substance. This invalidates all stored point data
     * @param substance - a string for the substance. Must be in valid_substances.
     */
    set_substance(substance){
        if (!substance in this.valid_substances){
            throw new Error("No a valid substance");
        }
        this.substance = substance;
        this.clearpoints();
        this.notify(this, PointModel.EVENT_SUBSTANCE, this.get_substance())
    }

    /**
     * Get all valid units for PMGI
     * @returns valid_units - dict of valid units, keys are unit category,
     *                             values are arrays of legal values
     */
    get_valid_units(){
        return this.valid_units;
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
    get_valid_properties(){
        return this.valid_substances[this.substance]['props'];
    }

    /**
     * Returns the input properties possible for the current substance
     * @returns {*} array of properties represented by strings
     */
    get_input_properties(){
        return this.valid_substances[this.substance]['inputs'];
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
     * Add a new point to the list
     * @param point - A dict keyed by property.
     */
    add_point(point){
        // If it's new, the keys might not exist yet, initialize array
        if (this.points.length === 0){
            this.points = {};
            this.points['ptid'] = [this.point_id];
            for (const key in point) {
                this.points[key] = [point[key]];
            }
        } else {
            this.points['ptid'].push(this.point_id);
            for (const key in point) {
                this.points[key].push(point[key]);
            }
        }
        this.point_id++;
        this.notify(this, PointModel.EVENT_POINT, this.get_points())
    }

    /**
     * Remove a point based on it's integer id
     * @param id - the integer id of the point (via 'ptid' property)
     */
    delete_point(id){
        let index = this.points['ptid'].indexOf(parseInt(id));
        for (const key in this.points) {
            this.points[key].splice(index, 1);
        }
        // If this was the last point, we want to clear things out.
        if (this.points['ptid'].length == 0){
            this.clearpoints();
        } else {
            this.notify(this, PointModel.EVENT_POINT, this.get_points());
        }
    }

    /**
     * Clear all points stored and get ready to start over.
     */
    clearpoints(){
        this.points = [];
        this.point_id = this.INIT_ID;
        this.notify(this, PointModel.EVENT_INIT, null);
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
        this.show_all = show_all;
        this.target = formHTMLid;
    }

    update(source, event, data){
        if (event == PointModel.EVENT_SUBSTANCE){
            this.set_value(data);
        }
    }

    /**
     * Set the value the selector should take
     * @param substance - A substance id as a string
     */
    set_value(substance){
        $(this.target).val(substance);
    }

    /**
     * Create the substance selector
     * @param substances - All possible substances, expected as dictionary with
     *                      keys of the substance id that will appear in the list.
     * @param current_value - The id of the value you want the selector to have
     * @param shortlist - A shortlist array of substance_ids to display in the list
     */
    init(substances, current_value=null, shortlist=null){

        let subsel = $(this.target);
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
        this.target = formHTMLid;
        this.unit_list_div = "#hideablelist"; // Target for the unit selects

        // Button to hide the whole form
        this.button_hide = "#unit_hide"

        // Buttons for apply/revert functionality since multiple options may change at once
        this.button_apply = "#unit_apply";
        this.button_revert = "#unit_revert";

        // Because these are callbacks they need "this" bound.
        this.apply_onclick = this.apply_onclick.bind(this);
        this.revert_onclick = this.revert_onclick.bind(this);
        $(this.button_apply).on("click", this.apply_onclick);
        $(this.button_revert).on("click", this.revert_onclick);

        this.hide_onclick = this.hide_onclick.bind(this);
        $(this.button_hide).on("click", this.hide_onclick);
    }


    update(source, event, data){
        if (event == PointModel.EVENT_UNIT){
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
                $(this.button_apply).show();
                $(this.button_revert).show();
            });
            // Add the objects to the form
            $(this.target).append($li.append($label).append($select));
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
            let selobj = $('[name="'+key+'"]');
            selobj.val(units[key]);
        });
    }

    /**
     * Get the current values in the form
     * @returns dict keyed by unit category, with string values for the selection
     */
    get_values(){
        // Convert the values to a dict
        return Object.fromEntries(new FormData($(this.target)[0]));
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
            $(this.button_apply).hide();
            $(this.button_revert).hide();
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
        $(this.button_apply).hide();
        $(this.button_revert).hide();
    }

    /**
     * User clicks the show/hide button
     */
    hide_onclick(){
        $(this.unit_list_div).toggle();
    }
}

/**
 * A class for managing the form that consists of property data entry
 */
class PropEntryView{
    constructor(formHTMLid) {
        this.target = formHTMLid;
        this.prop_table = "#propinput";
        this.prop_form = "#propform";

        this.get_button = "#get_props";
        this.post_button = "#post_props";

        // Since these are callbacks they need to be bound to this
        this.get_onclick = this.get_onclick.bind(this);
        this.post_onclick = this.post_onclick.bind(this);
        $(this.get_button).on("click", this.get_onclick);
        $(this.post_button).on("click", this.post_onclick);
    }

    update(source, event, data){
        if (event == PointModel.EVENT_SUBSTANCE) {
            let prop_vals = this.get_values();  // Retain values
            this.init(get_input_properties(), prop_vals);
        }
    }

    /**
     * Initialize things
     * @param input_properties - An array of input property strings
     * @param prop_values - a dict keyed by property and with string values
     */
    init(input_properties, prop_values=null) {
        this.create_propform(input_properties);
        this.set_form_values(prop_values);
    }

    /**
     * Build the form. Note that an extra HTML attribute of propvalue will be
     * used to specify the actual property string separate from the name.
     * @param props - an array of property strings
     */
    create_propform(props) {
        // Always start from scratch
        $(this.prop_table).empty();

        // Build a header
        let head = "<thead><tr>"
        props.forEach((prop) => {
            head = head + "<th>" + prop + "</th>";
        });
        head = head + "</tr></thead>";

        $(this.prop_table).append(head);

        // Build each input box
        let tr = $("<tr>")
        props.forEach((prop) => {
            let td = $("<td>");
            // Use string formatting to prevent insanity
            let inputbox = `<input type="text" propvalue="${prop}" id="${prop}_input" name="${prop}_input">`;
            tr.append(td.append(inputbox));
        });
        $(this.prop_table).append(tr);
    }

    /**
     * Copy existing values into the boxes
     * @param props - a dict keyed by property and with string values
     */
    set_form_values(props) {
        if (props != null) {
            $(this.prop_form + ' input').each((id, box) => {
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
        $(this.prop_form+ " input").each((id, box) =>{
            let value = box.value;
            if (value !== ""){ // If specified, add it to the prop dict
                let prop = box.attributes['propvalue'].nodeValue;
                outdata[prop] = value;
            }
        });
        return outdata;
    }

    /**
     * A callback to execute the GET operation. Probably not needed for deployment
     */
    get_onclick(){
        compute_point(this.get_values(), "GET");
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
    constructor(formHTMLid) {
        super();
        this.target = formHTMLid;
        this.hide_checks = "#propchoice_hide";
        this.prop_checks = "#propchecks";

        // Since these will be used as callbacks, they need to be bound
        this.checkbox_onchange = this.checkbox_onchange.bind(this);

        this.hide_onclick = this.hide_onclick.bind(this);
        $(this.hide_checks).on("click", this.hide_onclick);
    }

    update(source, event, data) {
        if (event == PointModel.EVENT_SUBSTANCE) {
            let disp_props = this.get_checkbox_values();
            this.init(get_valid_properties(), disp_props);
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

        this.notify(this,PropChooserView.EVENT_PROPERTY_VISIBILITY, this.get_checkbox_values());
    }

    /**
     * Build the checkboxes
     * @param valid_properties - an array of valid property strings
     */
    create_checkboxes(valid_properties) {
        $(this.prop_checks).empty();
        // Loop over all properties
        valid_properties.forEach(prop => {
            // The form will be a list of labelled check boxes
            let $li = $("<li>")
            let $label = $('<label>' + prop + '</label>', {});

            let $checkbox = $('<input>',{
                    type: "checkbox",
                    value: prop,
                    id: prop+'_box',
                    name: prop+'_box'
            });

            // add the callback
            $checkbox.on("click", this.checkbox_onchange);

            // Add the objects to the form
            $(this.prop_checks).append($li.append($label).append($checkbox));
        });
    }

    /**
     * Callback for when one of the checkboxes is changed
     */
    checkbox_onchange(){
        let disp_props = this.get_checkbox_values();
        this.notify(this, PropChooserView.EVENT_PROPERTY_VISIBILITY, disp_props);
    }

    /**
     * Get the values of the checkboxes
     * @returns names - an array of property strings that are checked
     */
    get_checkbox_values() {
        let names = [];
        $(this.prop_checks + ' input:checked').each((id, box) => {
            names.push(box.value);
        });
        return names;
    }

    /**
     * Set the values of the checkboxes
     * @param show_properties - an array of property strings that should be checked
     */
    set_checkbox_values(show_properties) {

        $(this.prop_checks + ' input').each((id, box) => {
            let prop = box.value;
            let checked = show_properties.includes(prop);
            if (checked) {
                box.checked = true;
            } else {
                box.checked = false;
            }
        });
    }

    /**
     * Toggle visibility of properties
     */
    hide_onclick(){
        $(this.prop_checks).toggle();
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
    constructor(divTarget) {
        // TODO - variable plot x- and y-axes
        // TODO - Additional background data, steam dome, isolines
        // TODO - variable display props in popups
        // TODO - axis labels, plot quality
        this.x_prop = 's';
        this.y_prop = 'T';
        this.dispprops = ['T','s','p','v'];
        this.target = divTarget;
        this.container = document.getElementById(divTarget);
        this.init();
    }

    init(){
        this.set_layout();
        // Create the plot trace
        let traces = [{
            x: [],
            y: [],
            customdata: [],
            mode: 'markers',
            hovertemplate: "<b> Point prop<br>"+
                this.x_prop+": %{x}<br>" +
                this.y_prop+": %{y}<br>" +
                "attr: %{customdata: .2f}",
            type: 'scatter'
        }];
        // Create the plot object
        Plotly.newPlot(this.container, traces, this.layout);
        this.setupPlotClickListener();
    }

    /**
     * Details for styling the plot
     */
    set_layout(){
        let x_scale;
        let y_scale;
        if (this.x_prop == 'v'){
            x_scale = 'log';
        } else {
            x_scale = 'linear';
        }
        if (this.y_prop == 'p'){
            y_scale = 'log';
        } else {
            y_scale = 'linear';
        }

        this.layout = {
            xaxis: {
                type: x_scale,
                autorange: true
            },
            yaxis: {
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
        let myPlot = this.container;
        let myPlotContainer = this;
        d3.select(".plotly").on('click', function(d, i) {
            var e = d3.event;
            var bgrect = document.getElementsByClassName('gridlayer')[0].getBoundingClientRect();
            var x = ((e.x - bgrect['x']) / (bgrect['width'])) * (myPlot.layout.xaxis.range[1] - myPlot.layout.xaxis.range[0]) + myPlot.layout.xaxis.range[0];
            var y = ((e.y - bgrect['y']) / (bgrect['height'])) * (myPlot.layout.yaxis.range[0] - myPlot.layout.yaxis.range[1]) + myPlot.layout.yaxis.range[1];
            if (x.between(myPlot.layout.xaxis.range[0], myPlot.layout.xaxis.range[1]) &&
                y.between(myPlot.layout.yaxis.range[0], myPlot.layout.yaxis.range[1])) {

                // Build the data and send to the controller
                let formData = {}
                formData[myPlotContainer.x_prop] = x
                formData[myPlotContainer.y_prop] = y
                compute_point(formData, "POST");
            }
        });
    }


    update(source, event, data){
        if (event == PointModel.EVENT_POINT){
            this.updatePoints(data);
        } else if (event == PointModel.EVENT_INIT) {
            this.init();
        } else if (event == PropChooserView.EVENT_PROPERTY_VISIBILITY){
            this.dispprops = data;
            this.updatePoints(get_points());
        }
    }

    /**
     * Handling points being added to the list of points
     * @param points
     */
    updatePoints(points) {
        // Build the customdata object for the tooltip
        // Object has the form [[h1,v1,s1],[h2,v2,s2],[h3,v3,s3]]

        let allkeys = Object.keys(points);
        if (allkeys.length >0) {
            let customdataset = [];  // The custom data that will be added to the tooltip
            let keylist = [];
            for (let i = 0; i < points['ptid'].length; i++) {  // Loop over all points
                let arr = [] // Build an array of all props for this index.
                arr.push(points['ptid'][i]); // Make the index the very first datapoint.

                allkeys.forEach(key => {
                    if (key !== this.x_prop &&
                        key !== this.y_prop &&
                        this.dispprops.includes(key)) {
                        if (i == 0) {
                            keylist.push(key);
                        }
                        arr.push(points[key][i]);
                    }
                });
                customdataset.push(arr);
            }

            // customdataset is now (ptid, T, p, v, ...)

            // Build the strings that identify the points
            let customrows = "";
            for (let i = 0; i < keylist.length; i++) {
                customrows = customrows + keylist[i] + ": %{customdata[" + (i + 1) + "]}<br>";
            }

            // Fully replace trace, including the custom data
            let update = {
                x: [points[this.x_prop]],
                y: [points[this.y_prop]],
                customdata: [customdataset],
                hovertemplate: "<b> Point %{customdata[0]}<br>" +
                    this.x_prop + ": %{x}<br>" +
                    this.y_prop + ": %{y}<br>" +
                    customrows,
            }
            // May need to adjust traceID when we accommodate the isolines, etc.
            Plotly.restyle(this.container, update, [0])
        }
    }
}

/**
 * A class for managing the interactive table
 */
class TableView{
    // TODO - Unit display in header?
    // delete rows? https://stackoverflow.com/questions/64526856/how-to-add-edit-delete-buttons-in-each-row-of-datatable
    // showhide columns https://datatables.net/examples/api/show_hide.html
    constructor(divTarget) {
        this.target = divTarget;
        this.table = null
    }

    init(props){
        this.dispprops = [...props]; // copy of props
        if (!this.dispprops.includes('ptid')){
            this.dispprops.unshift("ptid");// ptid should be in the table but not the prop list
        }

        // Can only init the table the very first time
        if (this.table == null){
            let $tablediv = $(this.target);
            $tablediv.empty();
            let $head = $('<thead></thead>');
            let $foot = $('<tfoot></tfoot>'); // Havent figured out the footer
            let $r = $('<tr></tr>')
            this.dispprops.forEach((prop) =>{
                let $th = $('<th>'+prop+'</th>');
                $r.append($th);
            });
            $r.append('<th>Ctrl</th>');
            $head.append($r);
            //$foot.append($r);
            $tablediv.append($head);
            //$tablediv.append($foot);


            // Build the data table with null content. Insert the delete button in the extra column.
            let table = new DataTable(this.target, {
                "columnDefs": [ {
                    "targets": -1,
                    "data": null,
                    "defaultContent": "<button id='click2del'>Delete</button>"
                } ]
            });

            // Click handler for each row's delete button
            $(this.target + ' tbody').on( 'click', 'button', function () {
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
        if (event == PointModel.EVENT_POINT){
            this.updatePoints(data);
        } else if (event == PointModel.EVENT_INIT) {
            this.init(get_valid_properties());
        } else if (event == PropChooserView.EVENT_PROPERTY_VISIBILITY) {
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
            if (columns.includes(name) || name=="ptid" || name=="Ctrl"){
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
var propEntryView;
var plotView;
var tableView;
var pointModel;


// Execute when the page loads
$(document).ready(function(){
    // Instantiate classes with their targets
    pointModel = new PointModel();
    unitFormView = new UnitFormView('#unitform');
    substanceFormView = new SubstanceFormView('#sel_substance');
    propChooserView = new PropChooserView("#property_selection")
    propEntryView = new PropEntryView("#property_controls")
    tableView = new TableView('#proptable');
    plotView = new PlotView("plot");

    // getInfo is an async request, so use the callback to complete setup.
    getInfo((data)=>{
        // Get the general info data, assign to model
        pointModel.init(data.valid_units, data.substances);
        pointModel.set_units(data.units);
        pointModel.set_substance(pointModel.DEFAULT_SUBSTANCE);

        // Assign views to listen to the main model
        pointModel.addListener(unitFormView);
        pointModel.addListener(substanceFormView);
        pointModel.addListener(tableView);
        pointModel.addListener(plotView);
        pointModel.addListener(propChooserView);
        pointModel.addListener(propEntryView);

        // Assign views to listen to the views that hold state data
        propChooserView.addListener(tableView);
        propChooserView.addListener(plotView);

        // Call inits on views now that the properties exist
        tableView.init(get_valid_properties());
        unitFormView.init(get_valid_units(), get_units());
        substanceFormView.init(get_valid_substances(), get_substance(), get_display_substances());
        propChooserView.init(get_valid_properties(), pointModel.DEFAULT_PROP_SHORTLIST);
        propEntryView.init(get_input_properties());
    });
});


// Passthrough controller functions that get/set on behalf of the model

function get_valid_properties(){
    // TODO - consider where this belongs
    return pointModel.get_valid_properties();
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

function set_substance(newsubstance){
    pointModel.set_substance(newsubstance);
}

function get_substance(){
    return pointModel.get_substance();
}

function get_units(){
    return pointModel.get_units();
}

function set_units(units){
    pointModel.set_units(units);
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
    if (mode == "GET"){
        $.get(requestroute, props, propResponseSuccess,dataType='json')
            .fail(propResponseFail);
    } else if (mode == "POST") {
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





