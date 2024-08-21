import SortableTable from "./SortableTable";
import FairnessPerformanceChart from './FairnessPerformanceChart';
import './ComparisonPage.css';
import React, {useEffect, useState} from "react";
import {Icon} from "@iconify/react";
import {BeatLoader} from "react-spinners";
import {stringToColor, toTitleCase} from "./Utils";
import {Button, Dialog, DialogActions, DialogContent, DialogTitle} from "@mui/material";
import {Bar} from "react-chartjs-2";
import axios from "axios";
import {BASE_BACKEND_URL} from "./api";

// import {ensembles} from "./tablesData";

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
    const [ensembleTables, setEnsembleTables] = useState(null);
    const [ensembleChart, setEnsembleChart] = useState(null);
    const [dialogIsLoading, setDialogIsLoading] = useState(false);
    const [dialogOpen, setDialogOpen] = useState(false);

    useEffect(() => {
        fetchData();
    }, [datasetId]);


    const fetchData = async () => {
        try {
            setIsLoading(true);
            const params = new URLSearchParams();

            params.append('sensitive_attribute', sensitiveAttribute);
            params.append('matching_threshold', matchingThreshold);
            matchers.forEach((matcher) => params.append('matchers', matcher));
            fairnessMetrics.forEach((metric) => params.append('fairness_metrics', metric));


            const response = await axios.get(`${BASE_BACKEND_URL}/v1/datasets/${datasetId}/ensemble/?${params}`, {
                headers: {
                    accept: 'application/json',
                },
            });
            console.log(response.data)
            setEnsembleTables(response.data.tables);
            setEnsembleChart(response.data.charts);
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handlePointClick = (event, element) => {
        setDialogOpen(false);
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
            {!isLoading && ensembleTables && (<div className="results-div">
                <div className="tables-div">
                    <h2><Icon inline={true} icon="majesticons:checkbox-list-detail-line"/> Metric Details</h2>
                    {Object.entries(ensembleTables).map(([title, data], index) => (
                        <SortableTable title={title} tableData={data}/>
                    ))}
                </div>
                <div className="diagram-div">
                    <h2><Icon icon="mdi:chart-box-outline" inline={true}/> Fairness Performance Tradeoff Chart</h2>
                    <FairnessPerformanceChart data={ensembleChart} handlePointClick={handlePointClick}/>
                    <p>The x-axis of this plot represents the unfairness of the matcher, while the y-axis captures the
                        performance of the model. A smaller value on the x-axis indicates a more fair setting, as it
                        signifies a model with unfairness closer to zero. For the y-axis, the desirability of a smaller
                        or larger value depends on the performance measure being considered. For instance, in the case
                        of the False Positive Rate Parity measure, a smaller value is desirable, while for the True
                        Positive Rate Parity measure, a larger value may be preferable.
                        Each point on the plot corresponds to an ensemble-based matching strategy and its associated
                        unfairness and performance values. Users can navigate through the Pareto frontier of each
                        measure and select a matching strategy that meets their preferred performance and fairness
                        constraints.</p>
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
                                {/*<SortableTable columns={ensembles.columns} data={ensembles.data} title="Ensembles"*/}
                                {/*               iconTitle="material-symbols:all-match-outline-rounded"/>*/}
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