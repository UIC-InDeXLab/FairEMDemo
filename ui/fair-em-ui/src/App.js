import React, { useEffect, useState } from 'react';
import Intro from './Intro';
import DatasetSelection from './DatasetSelection';
import MatcherSelection from './MatcherSelection';
import FairnessAnalysis from './FairnessAnalysis';
import './App.css';
import 'balloon-css';
import Navbar from './Navbar';
import axios from 'axios';
import { BASE_BACKEND_URL } from './api';
import ComparisonPage from "./ComparisonPage";

function App() {
    const [step, setStep] = useState(0); // Current step (0-3)
    const [datasetId, setDataset] = useState(null); // Stores uploaded dataset ID
    const [matchers, setMatchers] = useState([]); // Selected matchers
    const [disableNext, setDisableNext] = useState(false);
    const [explanationDict, setExplanationDict] = useState({});
    const [hoveredText, setHoveredText] = useState('');
    const [tooltipText, setTooltipText] = useState('');
    const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

    const [sensitiveAttribute, setSensitiveAttribute] = useState('');
    const [disparityCalculationType, setDisparityCalculationType] = useState('');
    const [fairnessMetrics, setFairnessMetrics] = useState([]);
    const [matchingThreshold, setMatchingThreshold] = useState(0.5)
    const [fairnessThreshold, setFairnessThreshold] = useState(0.5);
    const [groupAcceptanceCount, setGroupAcceptanceRate] = useState(10);
    const [groups, setGroups] = useState([]);

    useEffect(() => {
        // Fetch explanation JSON from the backend
        const fetchExplanation = async () => {
            try {
                const response = await axios.get(`${BASE_BACKEND_URL}/v1/definitions/`);
                setExplanationDict(response.data); // Assuming response.data is the dictionary
                console.log(response);
            } catch (error) {
                console.error('Error fetching explanation:', error);
            }
        };

        fetchExplanation();

        return () => {
            // Cleanup function
        };
    }, []);

    useEffect(() => {
        // Set tooltip text and position when hovering over text
        const handleMouseOver = (event) => {
            let text = ''
            try {
                text = event.target.innerText.trim().toLowerCase();
            } catch (e) {
            }
            if (explanationDict[text]) {
                const rect = event.target.getBoundingClientRect();
                setHoveredText(event.target.innerText.trim());
                setTooltipText(explanationDict[text]);
                setTooltipPosition({ x: rect.left, y: rect.bottom }); // Position below the word
            } else {
                setHoveredText('');
                setTooltipText('');
            }
        };

        document.body.addEventListener('mouseover', handleMouseOver);

        return () => {
            document.body.removeEventListener('mouseover', handleMouseOver);
        };
    }, [explanationDict]);

    const handleNext = () => {
        setStep(step + 1);
    };
    const handleBack = () => {
        setDisableNext(false);
        setStep(step - 1);
    };

    // Functions to handle data updates from child components

    return (
        <div>
            <Navbar step={step} disableNext={disableNext} onNext={handleNext} onBack={handleBack} />
            <div className="app-container">
                <div className="form-container">
                    {step === 0 && <Intro onNext={handleNext} />}
                    {step === 1 && (
                        <DatasetSelection
                            setDatasetId={setDataset}
                            setDisableNext={setDisableNext}
                            onNext={handleNext}
                        />
                    )}
                    {step === 2 && (
                        <MatcherSelection
                            datasetId={datasetId}
                            onNext={handleNext}
                            onBack={handleBack}
                            setMatchers={setMatchers}
                            setDisableNext={setDisableNext}
                        />
                    )}
                    {step === 3 && (
                        <FairnessAnalysis
                            datasetId={datasetId}
                            matchers={matchers}
                            onBack={handleBack}
                            setGlobalFairnessMetrics={setFairnessMetrics}
                            setGlobalGroups={setGroups}
                            setGlobalFairnessThreshold={setFairnessThreshold}
                            setGlobalDisparityCalculationType={setDisparityCalculationType}
                            setGlobalGroupAcceptanceCount={setGroupAcceptanceRate}
                            setGlobalMatchingThreshold={setMatchingThreshold}
                            setGlobalSensitiveAttribute={setSensitiveAttribute}
                            setDisableNext={setDisableNext}
                        />
                    )}
                    {step === 4 && (
                        <ComparisonPage
                            datasetId={datasetId}
                            matchers={matchers}
                            onBack={handleBack}
                            disparityCalculationType={disparityCalculationType}
                            matchingThreshold={matchingThreshold}
                            fairnessThreshold={fairnessThreshold}
                            fairnessMetrics={fairnessMetrics}
                            sensitiveAttribute={sensitiveAttribute}
                            groupAcceptanceCount={groupAcceptanceCount}
                        />
                    )}
                </div>
            </div>
            {hoveredText && tooltipText && (
                <div
                    className="balloon"
                    style={{ position: 'absolute', top: tooltipPosition.y, left: tooltipPosition.x }}
                >
                    {tooltipText}
                </div>
            )}
        </div>
    );
}

export default App;
