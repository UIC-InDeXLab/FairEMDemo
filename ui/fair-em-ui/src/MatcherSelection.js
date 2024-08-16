import React, {useEffect, useState} from 'react';
import axios from 'axios';
import {BASE_BACKEND_URL} from './api';
import './MatcherSelection.css';
import {Icon} from "@iconify/react";

function MatcherSelection({datasetId, onNext, setMatchers, setDisableNext}) {
    const [availableMatchers, setAvailableMatchers] = useState([]);
    const [selectedMatchers, setSelectedMatchers] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get(`${BASE_BACKEND_URL}/v1/options/`);
                setAvailableMatchers(response.data.matchers);
            } catch (error) {
                console.error('Error fetching matchers:', error);
            }
        };
        setDisableNext(true);
        fetchData();
    }, []);

    const handleSelect = (matcher) => {
        if (selectedMatchers.includes(matcher)) {
            setSelectedMatchers(selectedMatchers.filter((m) => m !== matcher));
        } else {
            setSelectedMatchers([...selectedMatchers, matcher]);
        }
    };

    const handleSelectAll = () => {
        setSelectedMatchers(availableMatchers);
    };

    const handleSubmit = async () => {
        if (!selectedMatchers.length) {
            alert('Please select at least one matcher');
            return;
        }

        setIsLoading(true);

        try {
            const response = await axios.get(`${BASE_BACKEND_URL}/v1/datasets/${datasetId}/preprocess/`, {
                headers: {
                    accept: 'application/json',
                },
            });

            const params = new URLSearchParams();
            selectedMatchers.forEach((matcher) => params.append('matchers', matcher));
            params.append('epochs', '1'); // Assuming epochs are always 1

            const matchResponse = await axios.get(
                `${BASE_BACKEND_URL}/v1/datasets/${datasetId}/match/?${params}`,
                {
                    headers: {
                        accept: 'application/json',
                    },
                }
            );

            setIsLoading(false);
            setMatchers(selectedMatchers);
            onNext();
        } catch (error) {
            console.error('Error during processing:', error);
            setIsLoading(false);
            alert('An error occurred. Please try again.');
        }
    };

    return (
        <div className="matcher-div">
            <h2><Icon inline={true} icon="material-symbols:match-word"/> Matchers</h2>
            <p>This section helps you select the most effective set of matchers for your entity matching task. Matchers are algorithms that compare entities and determine whether they represent the same real-world object. Choosing the right matcher combination can significantly impact the accuracy and efficiency of your matching process.</p>
            <div className="matchers-groups-div">
                <div className="neurals-div">
                <h3><Icon inline={true} icon="eos-icons:neural-network"/> Neural Matchers:</h3>
                    <ul className="matchers-list">
                        {availableMatchers
                            .filter((matcher) => ['ditto', 'mcan', 'deepmatcher', 'hiermatcher'].includes(matcher.toLowerCase()))
                            .map((matcher) => (
                                <li key={matcher} className="matcher-item">
                                    <div className="matcher-checkbox">
                                        <input
                                            type="checkbox"
                                            id={matcher}
                                            checked={selectedMatchers.includes(matcher)}
                                            onChange={() => handleSelect(matcher)}
                                        />
                                        <label htmlFor={matcher}>{matcher}</label>
                                    </div>
                                </li>
                            ))}
                    </ul>
                </div>
                <div className="nonneurals-div">
                    <h3><Icon inline={true} icon="ic:round-linear-scale"/> Non-Neural Matchers:</h3>
                    <ul className="matchers-list">
                        {availableMatchers
                            .filter((matcher) => !['ditto', 'mcan', 'deepmatcher', 'hiermatcher'].includes(matcher.toLowerCase()))
                            .map((matcher) => (
                                <li key={matcher} className="matcher-item">
                                    <div className="matcher-checkbox">
                                        <input
                                            type="checkbox"
                                            id={matcher}
                                            checked={selectedMatchers.includes(matcher)}
                                            onChange={() => handleSelect(matcher)}
                                        />
                                        <label htmlFor={matcher}>{matcher}</label>
                                    </div>
                                </li>
                            ))}
                    </ul>
                </div>
                <div className="navigation-buttons">
                    <div className="select-all-button">
                        <button onClick={handleSelectAll}>Select All</button>
                    </div>
                    <button onClick={handleSubmit} disabled={isLoading} className="navigation-button">
                        {isLoading ? 'Processing...' : 'Start Training'}
                    </button>
                </div>
            </div>

        </div>
    );
}

export default MatcherSelection;
