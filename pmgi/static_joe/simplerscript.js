
// Define the classes
var substanceID = "";

var unitModel;
var dataModel;




var unitFormView;

/**
 *
 */
function init_units(){
    getInfo((data) => {
        // Get the general info data, assign to model
        unitModel = new UnitModel(data.data.legalunits, data.units);
        unitFormView = new UnitFormView('unit_controls',
                                            unitModel.get_valid_units(),
                                            unitModel.get_units,
                                            unitModel.set_units);
        init_data();
    });
}

/**
 * Async request to get global info
 * @param callback - a function handle for the response success
 */
function getInfo(callback){
    // Get all the PM info.
    $.get("/info",
        callback,
        'json');  // Data type of the response.

}


// Execute when the page loads
function init_data() {
    // Instantiate classes with their targets
    dataModel = new DataModel(substanceID);
    calc_auxline()
    unitModel.addListener(dataModel);

    propEntryView = new PropEntryView("property_controls",
                                        dataModel.get_input_properties(),
                                        unitModel.get_units_for_prop(dataModel.get_input_properties()),
                                        compute_point);
    unitModel.addListener(propEntryView);


    propChooserView = new PropChooserView("property_selection", PropChooserView.EVENT_PROPERTY_VISIBILITY);
    isolineChooserView = new PropChooserView("isoline_selection", PropChooserView.EVENT_ISOLINE_VISIBILITY, ['T', 'd', 'p', 's', 'h', 'x']);
    propChooserView.init(dataModel.get_output_properties(), dataModel.DEFAULT_PROP_OUT_SHORTLIST);
    isolineChooserView.init(dataModel.get_output_properties(), ['T', 'p', 'x']);



    plotView = new PlotView("plot_display", dataModel, unitModel.get_units_for_prop, compute_point);
    dataModel.addListener(plotView);
    unitModel.addListener(plotView);
    propChooserView.addListener(plotView);
    isolineChooserView.addListener(plotView);
    plotView.init();


    // Assign views to listen to the main model
    tableView = new TableView('property_table', dataModel, unitModel.get_units_for_prop);
    dataModel.addListener(tableView);
    propChooserView.addListener(tableView);
    tableView.init(dataModel.get_output_properties());



}



/**
 * Async request for getting a state from the backend.
 * @param props - Dict with keys of property and numeric values
 * @param mode - GET/POST. Only POST can handle units with the request
 */
function compute_point(props){
    let requestroute = "/state";

    // Add the substance ID to props always
    props['id'] = dataModel.get_substance();

    // Build the data request
    let postData = Object.assign({}, props); // clone it
    postData.units = unitModel.get_units();  // add the units on
    $.ajax({
        url: requestroute,
        type: "POST",
        data: JSON.stringify(postData),
        dataType: "json",
        contentType: 'application/json; charset=utf-8',
        success: (data) =>{
                dataModel.add_point(data.data);
        },
    });
}



function calc_auxline(){
    if (dataModel.get_substance().startsWith('mp')){
        compute_auxline((data)=>{
            let sll = data.data['liquid'];
            let svl = data.data['vapor'];
            // concatenate vapor to liquid
            Object.keys(svl).forEach(key => {
                for (let i = svl[key].length; i > -1; i--) {
                    sll[key].push(svl[key][i]);
                }
            });
            dataModel.add_auxline('steamdome', sll, parent='global');
        });

        compute_auxline((data)=>{
            data.data.data.forEach((line)=>{
                dataModel.add_auxline('x', line, 'global');
            });
        },{'x': 0, 'default': true});
    }

    // Add a few types of lines
    ['p', 'T', 'd', 'h', 's'].forEach((prop_val)=>{
        compute_args = {};
        compute_args[prop_val] = 0;
        compute_args["default"] = true;
        compute_auxline((data)=>{
            data.data.data.forEach((line)=>{
                dataModel.add_auxline(prop_val, line, 'global');
            });
        },compute_args);
    })
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
    props['id'] = dataModel.get_substance();

    if (mode === "GET"){
        $.get(requestroute, props, callback,dataType='json');
    } else if (mode === "POST") {
        let postData = Object.assign({}, props); // clone it
        postData.units = unitModel.get_units();  // add the units on
        $.ajax({
            url: requestroute,
            type: "POST",
            data: JSON.stringify(postData),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            success: callback
        });
    }
}


function init_page(){
    let selection = document.getElementById('selection_id');
    substanceID = get_cookie('idstr');
    selection.innerHTML = substanceID;
    if (substanceID !== "") {
        // Begin overall initialization
        init_units();
    }
}


// This is a general purpose function that navigates to the selection
// after setting the "from" cookie.  From is used to navigate back to
// the source page after having selected a substance.
function selection_go(from){
    set_cookie('from',from);
    window.location = '/selector';
}