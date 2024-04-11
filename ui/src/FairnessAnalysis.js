import React, {useEffect, useState} from 'react';
import axios from 'axios';
import {Bar} from 'react-chartjs-2';
import {BASE_BACKEND_URL} from './api';
import {Chart, registerables} from 'chart.js';
import './FairnessAnalysis.css';
import './Dialog.css';
import {Button, Dialog, DialogActions, DialogContent, DialogTitle} from '@mui/material';
import {explanationData} from "./explanationData";
import SortableTable from "./SortableTable";
import {BeatLoader} from 'react-spinners';
import {confusionMatrix, groupCoverage} from "./tablesData";
import {Icon} from '@iconify/react';
import annotationPlugin from 'chartjs-plugin-annotation';
import {stringToColor, toTitleCase} from "./Utils";

Chart.register(...registerables, annotationPlugin);

function FairnessAnalysis({
                              datasetId, matchers, onBack, onNext, setDisableNext, setGlobalSensitiveAttribute,
                              setGlobalDisparityCalculationType, setGlobalFairnessMetrics, setGlobalMatchingThreshold,
                              setGlobalFairnessThreshold, setGlobalGroupAcceptanceCount, setGlobalGroups
                          }) {
    const [fairnessData, setFairnessData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [selectedBarData, setSelectedBarData] = useState(null); // To store clicked bar data
    const [dialogIsLoading, setDialogIsLoading] = useState(false);

    // Control panel state
    const [selectedSensitiveAttribute, setSelectedSensitiveAttribute] = useState('');
    const [selectedDisparityCalculationType, setSelectedDisparityCalculationType] = useState('');
    const [selectedFairnessMetrics, setSelectedFairnessMetrics] = useState([]);
    const [matchingThreshold, setMatchingThreshold] = useState(0.5); // Default value
    const [fairnessThreshold, setFairnessThreshold] = useState(0.5); // Default value
    const [groupAcceptanceCount, setGroupAcceptanceCount] = useState(10); // Default value
    const [onlyShowUnfairGroups, setOnlyShowUnfairGroups] = useState(false);
    const [disparityCalculationTypes, setDisparityCalculationTypes] = useState([]);
    const [fairnessMeasures, setFairnessMeasures] = useState([]);
    const [datasetColumns, setDatasetColumns] = useState([]);
    const [selectedFairnessParadigm, setSelectedFairnessParadigm] = useState('Single Fairness'); // Default value
    const [groupsUpdated, setGroupsUpdated] = useState(false);

    const fetchData = async () => {
        setIsLoading(true);
        setDisableNext(true);
        try {
            const params = new URLSearchParams();
            matchers.forEach((matcher) => params.append('matchers', matcher));
            selectedFairnessMetrics.forEach((metric) => params.append('fairness_metrics', metric));
            params.append('sensitive_attribute', selectedSensitiveAttribute);
            params.append('disparity_calculation_type', selectedDisparityCalculationType);
            params.append('matching_threshold', matchingThreshold);
            params.append('fairness_threshold', fairnessThreshold);
            params.append('group_acceptance_count', groupAcceptanceCount);

            const response = await axios.get(`${BASE_BACKEND_URL}/v1/datasets/${datasetId}/fairness/?${params}`, {
                headers: {
                    accept: 'application/json',
                },
            });
            setFairnessData(response.data);
            setDisableNext(false);
        } catch (error) {
            console.error('Error fetching fairness results:', error);
            setError('Failed to load fairness analysis results.');
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        const fetchOptions = async () => {
            const optionsResponse = await axios.get(`${BASE_BACKEND_URL}/v1/options/`);
            setDisparityCalculationTypes(optionsResponse.data.disparity_calculation_types);
            setFairnessMeasures(optionsResponse.data.fairness_measures);
        };

        const fetchColumns = async () => {
            const columnsResponse = await axios.get(`${BASE_BACKEND_URL}/v1/datasets/${datasetId}/`);
            setDatasetColumns(columnsResponse.data.columns);
        };

        fetchOptions();
        fetchColumns();
    }, [datasetId]);

    const getBarChartData = (data) => {
        const datasets = [];
        const labels = new Set();

        Object.entries(data).forEach(([fairnessMeasure, d]) => {
            const fd = onlyShowUnfairGroups ? d.filter((item) => item.is_fair === false) : d;
            fd.map((item) => item.sens_attr).forEach((attr) => labels.add(attr));
        });

        Object.entries(data).forEach(([fairnessMeasure, d]) => {
            let filteredData = d;
            if (onlyShowUnfairGroups) {
                filteredData = d.filter((item) => {
                    return item.is_fair === false;
                });
            }
            datasets.push({
                label: toTitleCase(fairnessMeasure),
                data: filteredData.map((item) => item.disparities),
                backgroundColor: filteredData.map((item) => stringToColor(fairnessMeasure, 0.3)),
                borderColor: filteredData.map((item) => stringToColor(fairnessMeasure, 1)),
                borderWidth: 1.5,
                minBarLength: 3,
                isFair: filteredData.map((item) => item.is_fair),
            });
        });
        if (!groupsUpdated) {
            setGlobalGroups(Array.from(labels));
            setGroupsUpdated(true);
        }
        return {
            labels: Array.from(labels),
            datasets: datasets
        };
    };

    const handleSensitiveAttributeChange = (e) => {
        setSelectedSensitiveAttribute(e.target.value);
        setGlobalSensitiveAttribute(e.target.value);
    }

    const handleDisparityCalculationTypeChange = (e) => {
        setSelectedDisparityCalculationType(e.target.value);
        setGlobalDisparityCalculationType(e.target.value);
    }

    const handleFairnessMetricsChange = (e) => {
        setSelectedFairnessMetrics(Array.from(e.target.selectedOptions, (option) => option.value));
        setGlobalFairnessMetrics(Array.from(e.target.selectedOptions, (option) => option.value));
    }

    const handleMatchingThresholdChange = (e) => {
        setMatchingThreshold(Number(e.target.value));
        setGlobalMatchingThreshold(Number(e.target.value));
    }

    const handleFairnessThresholdChange = (e) => {
        setFairnessThreshold(Number(e.target.value));
        setGlobalFairnessThreshold(Number(e.target.value));
    }

    const handleGroupAcceptanceCount = (e) => {
        setGroupAcceptanceCount(Number(e.target.value));
        setGlobalGroupAcceptanceCount(Number(e.target.value));
    }


    const handleBarClick = (event, element) => {
        setDialogOpen(true);
        setDialogIsLoading(true);
        setTimeout(() => {
            setDialogIsLoading(false);
        }, 3143);
    };

    const getTooltipCallbacks = () => ({
        callbacks: {
            label: (context) => {
                const index = context.dataIndex;
                const label = toTitleCase(context.dataset.label);
                const value = context.dataset.data[index].toFixed(3);
                const fairness = context.dataset.isFair[index];
                return [`${label}: ${value}`, `Fair: ${fairness ? 'Yes' : 'No'}`];
            },
        },
        titleFont: {
            size: 16
        },
        bodyFont: {
            size: 14
        }
    });

    const getExplanationTable = () => {
        return (
            <SortableTable title="cn / False Negative Samples" data={explanationData.data} columns={explanationData.columns}
                           iconTitle="material-symbols-light:tab-group-outline-rounded"></SortableTable>
        );
    };

    const getGroupCoverage = () => {
        return (
            <SortableTable title="Coverage" columns={groupCoverage.columns}
                           data={groupCoverage.data} iconTitle="codicon:debug-coverage"></SortableTable>
        )
    };

    const getConfusionMatrix = () => {
        return (
            <SortableTable title="Confusion Matrix" columns={confusionMatrix.columns}
                           data={confusionMatrix.data} iconTitle="mdi:matrix"></SortableTable>
        )
    };

    return (<div className="fairness-analysis-container">
        <div className="control-panel">
            <h3><Icon inline={true} icon="material-symbols:display-settings-outline-rounded"/> Control Panel</h3>
            <label>
                Sensitive Attribute:
                <select
                    value={selectedSensitiveAttribute} onChange={handleSensitiveAttributeChange}>
                    <option value="">Select</option>
                    {datasetColumns.map((column) => (<option key={column} value={column}>
                        {column}
                    </option>))}
                </select>
            </label>

            <label>
                Disparity Calculation Type:
                <select value={selectedDisparityCalculationType} onChange={handleDisparityCalculationTypeChange}>
                    <option value="">Select</option>
                    {disparityCalculationTypes.map((type) => (<option key={type} value={type}>
                        {type}
                    </option>))}
                </select>
            </label>

            <label>
                Fairness Metrics:
                <select multiple value={selectedFairnessMetrics} onChange={handleFairnessMetricsChange}>
                    {fairnessMeasures.map((measure) => (<option key={measure} value={measure}>
                        {measure}
                    </option>))}
                </select>
            </label>

            <label>
                Matching Threshold:
                <input type="number" value={matchingThreshold} onChange={handleMatchingThresholdChange}/>
            </label>

            <label>
                Fairness Threshold:
                <input type="number" value={fairnessThreshold} onChange={handleFairnessThresholdChange}/>
            </label>

            {/*<label>*/}
            {/*    Group Acceptance Count:*/}
            {/*    <input type="number" value={groupAcceptanceCount} onChange={handleGroupAcceptanceCount}/>*/}
            {/*</label>*/}
            <label>
                Fairness Paradigm:
                <select
                    value={selectedFairnessParadigm}
                    onChange={(e) => setSelectedFairnessParadigm(e.target.value)}
                >
                    <option value="Single Fairness">Single Fairness</option>
                    <option value="Pairwise Fairness">Pairwise Fairness</option>
                    <option value="Both">Both</option>
                </select>
            </label>

            <label>
                Only Show Unfair Groups:
                <input
                    type="checkbox"
                    checked={onlyShowUnfairGroups}
                    onChange={(e) => setOnlyShowUnfairGroups(e.target.checked)}
                />
            </label>
            <button onClick={fetchData}>Analyze Fairness</button>
        </div>

        {isLoading && (
            <div className="center-content">
                <BeatLoader size={15} color={'#6285A2'} loading={isLoading}/>
                Analysing Fairness ...
            </div>
        )}
        {error && <p style={{color: 'red'}}>{error}</p>}
        {!isLoading && fairnessData && (<div className="matcher-grid">
            {Object.keys(fairnessData).map((matcher) => (<div key={matcher} className="matcher-section">
                <h3><Icon inline={true} icon="material-symbols:match-word"/> {matcher}</h3>
                <div className="fairness-grid">
                    {selectedFairnessParadigm === 'Single Fairness' || selectedFairnessParadigm === 'Both' ? (
                        <div className="fairness-section">
                            <h4><Icon inline={true} icon="gis:measure-line"/> Single Fairness</h4>
                            <div className="fairness-grid">
                                <Bar data={getBarChartData(fairnessData[matcher].single_fairness)}
                                     options={{
                                         onClick: handleBarClick,
                                         plugins: {
                                             tooltip: getTooltipCallbacks(),
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
                                         fairnessParadigm: selectedFairnessParadigm,
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
                                                 ticks: {
                                                     font: {
                                                         size: 13, // Set the font size for y-axis ticks
                                                     },
                                                 },
                                             },
                                         },
                                     }}/>
                            </div>
                        </div>) : null}
                    {selectedFairnessParadigm === 'Pairwise Fairness' || selectedFairnessParadigm === 'Both' ? (
                        <div className="fairness-section">
                            <h4><Icon inline={true} icon="gis:measure-area"/> Pairwise Fairness</h4>
                            <div className="fairness-grid">
                                <Bar data={getBarChartData(fairnessData[matcher].pairwise_fairness)}
                                     options={{
                                         onClick: handleBarClick,
                                         plugins: {
                                             tooltip: getTooltipCallbacks(),
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
                                         fairnessParadigm: selectedFairnessParadigm,
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
                                                 ticks: {
                                                     font: {
                                                         size: 13, // Set the font size for y-axis ticks
                                                     },
                                                 },
                                             },
                                         },
                                     }}/>
                            </div>
                        </div>) : null}
                </div>
            </div>))}
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
                    minWidth: '1200px', // Set maximum width (optional)
                    // maxHeight: '600px', // Set maximum height (optional)
                },
            }}
        >
            <DialogTitle><Icon icon="material-symbols:indeterminate-question-box" inline={true}/> DeepMatcher</DialogTitle>
            <DialogContent>
                {dialogIsLoading && (
                    <div className="center-content">
                        <BeatLoader size={15} color={'#6285A2'} loading={dialogIsLoading}/>
                        Loading Selected Group Details ...
                    </div>
                )}
                {!dialogIsLoading && (
                    <div className="dialog-div">
                        <div className="dialog-example-div">
                            <h3><Icon icon="ph:eyedropper-sample-fill" inline={true}/> Samples From Original Data Set
                            </h3>
                            {getExplanationTable()}
                        </div>
                        <div className="dialog-coverage-confusion-div">
                            <div className="dialog-coverage-div">
                                <h3><Icon inline={true} icon="nimbus:stats"></Icon> Group Statistics</h3>
                                {getGroupCoverage()}
                            </div>
                            <div className="dialog-confusion-div">
                                {getConfusionMatrix()}
                            </div>
                        </div>
                    </div>)}
            </DialogContent>
            <DialogActions>
                <Button onClick={() => setDialogOpen(false)}>OK</Button>
            </DialogActions>
        </Dialog>
    </div>);
}

export default FairnessAnalysis;
