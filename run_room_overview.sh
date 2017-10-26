#!/bin/bash
BOOKINGS_DIR=../tutor-planner-data/bookings
lsf-to-xlsx() {
    python -m source lsf-to-xlsx --export-capacity --lsf-xml-input-files="../tutor-planner-data/bookings-from-lsf/*.xml" --csv-input-files="../tutor-planner-data/bookings/own_bookings.csv" --maximal-tutorial-size=35 "$@"
}
echo "Export MAR,FH"
lsf-to-xlsx --include="MAR .*|FH .*" --type="tutorial" $BOOKINGS_DIR/raumbuchungen_tutorium_mar_fh.xlsx
echo "Export NOT MAR,FH"
lsf-to-xlsx --exclude="MAR .*|FH .*" --type="tutorial" $BOOKINGS_DIR/raumbuchungen_tutorium_NOT_mar_fh.xlsx
echo "Export TEL"
lsf-to-xlsx --include="TEL .*" --type="exercise"  $BOOKINGS_DIR/raumbuchungen_pool_TEL.xlsx
echo "Export Pool ALL"
lsf-to-xlsx --type="exercise" $BOOKINGS_DIR/raumbuchungen_pool_ALL.xlsx
echo "Export ALL ALL"
lsf-to-xlsx  $BOOKINGS_DIR/raumbuchungen_ALL.xlsx
