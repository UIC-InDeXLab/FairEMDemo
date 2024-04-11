import SortableTable from "./SortableTable";
import FairnessPerformanceChart from './FairnessPerformanceChart';
import './ComparisonPage.css';
import React, {useEffect, useState} from "react";
import {paretoData} from "./paretoData";
import {Icon} from "@iconify/react";
import {BeatLoader} from "react-spinners";
import {stringToColor, toTitleCase} from "./Utils";
import {Button, Dialog, DialogActions, DialogContent, DialogTitle} from "@mui/material";
import {Bar} from "react-chartjs-2";
import {ensembles} from "./tablesData";

function ComparisonPage({
                            datasetId,
                            matchers,
                            onBack,
                            disparityCalculationType,
                            fairnessThreshold,
                            matchingThreshold,
                            fairnessMetrics,
                            sensitiveAttribute,
                            groupAcceptanceCount, groups
                        }) {
    const [isLoading, setIsLoading] = useState(true);
    const [fetchedData, setFetchedData] = useState([]);
    const [dialogIsLoading, setDialogIsLoading] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);

    useEffect(() => {
        fetchData();
    }, [datasetId]);


    const fetchData = async () => {
        try {
            setTimeout(() => {
                setFetchedData([
                    {
                        columns: [
                            {key: 'matcher', label: 'Matcher'},
                            {key: 'cn', label: 'cn'},
                            {key: 'de', label: 'de'},
                        ],
                                data: [
                                    {matcher: "DeepMatcher", cn: 0.48, de: 0.72},
                                    {matcher: "HierMatcher", cn: 0.47, de: 0.78},
                                    {matcher: "Ditto", cn: 0.59, de: 0.85},
                                    {matcher: "MCAN", cn: 0.40, de: 0.70},
                                    {matcher: "LinRegMatcher", cn: 0.33, de: 0.23}
                                ]
                    },
                    {
                        columns: [
                            {key: 'matcher', label: 'Matcher'},
                            {key: 'cn', label: 'cn'},
                            {key: 'de', label: 'de'},
                        ],
                        data: [
                            {matcher: "DeepMatcher", cn: 0.79, de: 0.87},
                            {matcher: "HierMatcher", cn: 0.78, de: 0.89},
                            {matcher: "Ditto", cn: 0.77, de: 0.94},
                            {matcher: "MCAN", cn: 0.86, de: 0.94},
                            {matcher: "LinRegMatcher", cn: 0.44, de: 0.96}
                        ]
                    }
                ]);
                setIsLoading(false);
            }, 4379);
        } catch (error) {
            console.error(error);
            setIsLoading(false);
        }
    };

    const handlePointClick = (event, element) => {
        setDialogOpen(true);
    }

    const getBarChartData = (data) => {
        const datasets = [];
        const labels = new Set();

        labels.add("cn")
        labels.add("de")

        const fairnessMeasure = "positive_predictive_value_parity"
        const filteredData = [{"disparities": 0.01, "is_fair": "True"}, {"disparities": 0.01, "is_fair": "True"},]
        datasets.push({
            label: toTitleCase(fairnessMeasure),
            data: filteredData.map((item) => item.disparities),
            backgroundColor: filteredData.map((item) => stringToColor(fairnessMeasure, 0.3)),
            borderColor: filteredData.map((item) => stringToColor(fairnessMeasure, 1)),
            borderWidth: 1.5,
            minBarLength: 3,
            isFair: filteredData.map((item) => item.is_fair),
        })

        return {
            labels: Array.from(labels),
            datasets: datasets
        };
    };

    return (
        <div className="comparison-div">
            {isLoading && (
                <div className="center-content">
                    <BeatLoader size={15} color={'#6285A2'} loading={isLoading}/>
                    Creating Ensemble of Matchers ...
                </div>
            )}
            {!isLoading && fetchedData && (<div className="results-div">
                <div className="tables-div">
                    <h2><Icon inline={true} icon="majesticons:checkbox-list-detail-line"/> Metric Details</h2>
                    {fairnessMetrics.map((metric, index) => {
                        return (
                            <SortableTable
                                className="sortable-table"
                                title={toTitleCase(metric.toString().replace("Parity", ""))}
                                data={fetchedData[index].data}
                                columns={fetchedData[index].columns}
                            />
                        );
                    })}
                </div>
                <div className="diagram-div">
                    <h2><Icon icon="mdi:chart-box-outline" inline={true}/> Fairness Performance Tradeoff Chart</h2>
                    <FairnessPerformanceChart data={paretoData} handlePointClick={handlePointClick}/>
                    <p>The x-axis of this plot represents the unfairness of the matcher, while the y-axis captures the performance of the model. A smaller value on the x-axis indicates a more fair setting, as it signifies a model with unfairness closer to zero. For the y-axis, the desirability of a smaller or larger value depends on the performance measure being considered. For instance, in the case of the False Positive Rate Parity measure, a smaller value is desirable, while for the True Positive Rate Parity measure, a larger value may be preferable.
                        Each point on the plot corresponds to an ensemble-based matching strategy and its associated unfairness and performance values. Users can navigate through the Pareto frontier of each measure and select a matching strategy that meets their preferred performance and fairness constraints.</p>
                </div>
            </div>)}
            <Dialog
                open={dialogOpen}
                keepMounted
                onClose={() => setDialogOpen(false)}
                aria-describedby="alert-dialog-slide-description"
                sx={{
                    '& .MuiDialog-paper': {
                        backgroundColor: 'white', // Adjust background color here
                        borderRadius: '10px', // Set dialog radius
                        minWidth: '800px', // Set maximum width (optional)
                        // maxHeight: '600px', // Set maximum height (optional)
                    },
                }}
            >
                <DialogTitle><Icon icon="material-symbols:indeterminate-question-box"/></DialogTitle>
                <DialogContent>
                    {dialogIsLoading && (
                        <div className="center-content">
                            <BeatLoader size={15} color={'#6285A2'} loading={dialogIsLoading}/>
                            Loading Ensemble of Matchers Results ...
                        </div>
                    )}
                    {!dialogIsLoading && (
                        <div className="dialog-div">
                            <div className="dialog-example-div">
                                <h3><Icon icon="mdi:chart-box-outline" inline={true}/> Ensemble Performance Chart</h3>
                                <Bar data={getBarChartData(null)}
                                     options={{
                                         plugins: {
                                             legend: {
                                                 labels: {
                                                     font: {
                                                         size: 14
                                                     }
                                                 }
                                             },
                                             annotation: {
                                                 annotations: {
                                                     line1: {
                                                         type: 'line',
                                                         yMin: fairnessThreshold,
                                                         yMax: fairnessThreshold,
                                                         borderColor: '#bf6b99',
                                                         borderWidth: 3,
                                                         borderDash: [5, 5],
                                                         label: {
                                                             backgroundColor: '#b33b72',
                                                             content: 'Fairness Threshold',
                                                             display: true
                                                         },
                                                     }
                                                 }
                                             }
                                         },
                                         scales: {
                                             x: {
                                                 title: {
                                                     display: true,
                                                     text: 'Groups',
                                                     font: {
                                                         size: 13, // Set the font size for x-axis title
                                                     },
                                                 },
                                                 ticks: {
                                                     font: {
                                                         size: 13, // Set the font size for x-axis ticks
                                                     },
                                                 },
                                             },
                                             y: {
                                                 title: {
                                                     display: true,
                                                     text: 'Disparity',
                                                     font: {
                                                         size: 13, // Set the font size for y-axis title
                                                     },
                                                 },
                                                 max: fairnessThreshold * 1.1,
                                                 ticks: {
                                                     font: {
                                                         size: 13, // Set the font size for y-axis ticks
                                                     },
                                                 },
                                             },
                                         },
                                     }}/>
                            </div>
                            <div className="dialog-example-div">
                                <h3><Icon icon="icon-park-outline:full-selection" inline={true}/> Selected Ensembles
                                </h3>
                                <SortableTable columns={ensembles.columns} data={ensembles.data} title="Ensembles"
                                               iconTitle="material-symbols:all-match-outline-rounded"/>
                            </div>
                        </div>)}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDialogOpen(false)}>OK</Button>
                </DialogActions>
            </Dialog>
        </div>
    )

}

export default ComparisonPage;