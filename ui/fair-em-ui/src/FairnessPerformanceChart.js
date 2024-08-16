import React from 'react';
import {Scatter} from 'react-chartjs-2';
import {stringToColor, toTitleCase} from "./Utils";

const FairnessPerformanceChart = ({data, handlePointClick}) => {
    const isParetoFrontier = (point, data, xObj = "min", yObj = "min") => {
        for (const otherPoint of data) {
            let xCondition = false;

            if (xObj === "min") {
                xCondition = otherPoint.disparity < point.disparity;
            } else if (xObj === "max") {
                xCondition = otherPoint.disparity > point.disparity;
            }

            let yCondition = false;
            if (yObj === "min") {
                yCondition = otherPoint.performance < point.performance;
            } else if (yObj === "max") {
                yCondition = otherPoint.performance > point.performance;
            }

            if (xCondition && yCondition) {
                return false;
            }
        }
        return true;
    };

    const getTooltipCallbacks = () => ({
        callbacks: {
            label: (context) => {
                const index = context.dataIndex;
                const matchers = context.dataset.data[index].matchers
                const x = context.dataset.data[index].x
                const y = context.dataset.data[index].y
                return [
                    `Metric: ${context.dataset.label}`,
                    `Disparity: ${x.toFixed(3)}, Performance: ${y.toFixed(3)}`,
                    ...Object.entries(matchers).map(([key, value]) => `${key}: ${value}`),
                ];
            },
        },
        titleFont: {
            size: 16
        },
        bodyFont: {
            size: 14
        },
    });

    const chartOptions = {
        onClick: handlePointClick,
        plugins: {
            tooltip: getTooltipCallbacks(),
            legend: {
                labels: {
                    font: {
                        size: 15
                    }
                }
            }
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Disparity Between Max and Min Group Performance',
                    font: {
                        size: 16, // Set the font size for x-axis title
                    },
                },
                min: 0,
                max: 1.8,
                ticks: {
                    font: {
                        size: 14, // Set the font size for x-axis ticks
                    },
                },
            },
            y: {
                title: {
                    display: true,
                    text: 'Worst Performance Between Groups',
                    font: {
                        size: 16, // Set the font size for y-axis title
                    },
                },
                min: 0,
                max: 1,
                ticks: {
                    font: {
                        size: 14, // Set the font size for y-axis ticks
                    },
                },
            },
        },
        elements: {
            point: {
                radius: 8, // Increase the radius of points
            },
        },
    };

    const chartData = {
        datasets: data.map((dataset, index) => ({
            label: toTitleCase(toTitleCase(dataset.name)),
            data: dataset.data.map((point) => ({
                x: point.disparity ,
                y: point.performance ,
                matchers: point.matchers,
            })),
            pointBackgroundColor: dataset.data.map(
                (point) =>
                    isParetoFrontier(point, dataset.data, dataset.xObj, dataset.yObj)
                        ? stringToColor(dataset.name, 0.5)
                        : stringToColor(dataset.name, 0.1)
            ),
            pointBorderColor: dataset.data.map(
                (point) =>
                    isParetoFrontier(point, dataset.data, dataset.xObj, dataset.yObj)
                        ? stringToColor(dataset.name, 0.9)
                        : stringToColor(dataset.name, 0.2)
            ),
        })),
    };

    return (
        <div>
            <Scatter data={chartData} options={chartOptions}/>
        </div>
    );
};

export default FairnessPerformanceChart;
