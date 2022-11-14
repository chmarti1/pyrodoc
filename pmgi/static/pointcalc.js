var DEFAULT_IDSTR = "mp.H2O";
var infodata;

var unitModel;
var dataModel;

var unitPickerView;

var propEntryView;
var propChooserView;
var plotView;
var tableView;

var substancePicker;


var plotControls;

// document.ready()
$(function(){

    // Check if the infodata has been created. If not, get it from ajax and reload
    infodata = localStorage.getItem("infodata");
    if (infodata === null){
        ajax_info((data)=>{
            localStorage.setItem("infodata", JSON.stringify(data));
            infodata = data;
            init();
        });
    } else {
        infodata = JSON.parse(infodata);
        init();
    }
});

function init(){
    // Infodata has now been initialized

    let subid = load_substance_choice();
    let units = load_units_choice();

    $("#substance_title").text("Substance: "+subid);

    dataModel = new DataModel(subid);
    unitModel = new UnitModel(infodata.data.legalunits, units);

    substancePicker = new ModalSubstancePicker('modal_substancepicker',
        '../static/modal_substance.html',
        infodata.data.substances);

    unitPickerView = new UnitFormView($('#modal_unitspicker'),
        "../static/unitspicker.html",
        infodata.data.legalunits,
        units,
        infodata.units,
        apply_units,
        onclick_changeunits);


    calc_auxline();

    propEntryView = new PropEntryView("property_controls",
        dataModel.get_input_properties(),
        unitModel.get_units_for_prop(dataModel.get_input_properties()),
        compute_point);


    propChooserView = new PropChooserView($("#property_selection_outer"), PropChooserView.EVENT_PROPERTY_VISIBILITY);

    plotControls = new PlotControls($("#plot_controls"), "../static/plot_options.html", true);

    plotView = new PlotView("plot_display", dataModel, unitModel.get_units_for_prop, compute_point);
    dataModel.addListener(plotView);
    propChooserView.addListener(plotView);
    plotControls.addListener(plotView);
    plotView.init();

    // Assign views to listen to the main model
    tableView = new TableView('property_table', dataModel, unitModel.get_units_for_prop);
    dataModel.addListener(tableView);
    propChooserView.addListener(tableView);
    tableView.init(dataModel.get_output_properties());

    propChooserView.init(dataModel.get_output_properties(), dataModel.DEFAULT_PROP_OUT_SHORTLIST);
    plotControls.init(dataModel.get_output_properties());


}

function load_substance_choice(){
    let sub = get_cookie("idstr");
    if (sub === ""){
        change_substance(DEFAULT_IDSTR);
    } else {
        display_substance(sub);
    }
    return sub;
}
function load_units_choice() {
    let actual = get_cookie("units");

    // If the unit data isn't set, initialize it.
    if (actual === "") {
        change_units(infodata.units);
    } else {
        actual = JSON.parse(actual);
        display_units(actual);
    }
    return actual;
}


function apply_units(units){
    unitPickerView.toggle();
    change_units(units)
}

function onclick_changesubstance(){
    substancePicker.toggle();
}


function onclick_changeunits(){
    unitPickerView.toggle();
}

function onclick_showplotcontrols(){
    plotControls.toggle();
}

function onclick_tableprop_checks(){
    propChooserView.toggle();
}

function change_substance(substance){
    set_cookie("idstr", substance);
    location.reload();
}

function change_units(units){
    set_cookie("units", JSON.stringify(units));
    location.reload();
}

function display_substance(sub){
    $("#sub_string").text(sub);
}

function display_units(units){
    $("#unit_string").text(JSON.stringify(units));
}

function ajax_info(callback){
    $.get("/info",
        callback,
        'json');  // Data type of the response.
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
            if (data.message.error){
                alert(data.message.message);
            } else {
                dataModel.add_point(data.data);
            }
        },
    });
}
