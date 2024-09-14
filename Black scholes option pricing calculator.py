import numpy as np
import math as m
from scipy.stats import norm
import tkinter as tk
from tkinter import ttk

def black_scholes(S, K, T, r, sigma, option_type='call'):
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == 'call':
        option_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == 'put':
        option_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")
    
    return option_price

def calculate_prices():
    S = float(entry_S.get())
    K = float(entry_K.get())
    T = float(entry_T.get())
    r = float(entry_r.get())
    sigma = float(entry_sigma.get())
    
    call_price = black_scholes(S, K, T, r, sigma, option_type='call')
    put_price = black_scholes(S, K, T, r, sigma, option_type='put')
    
    label_call_price.config(text=f"Call Option Price: {call_price:.2f}")
    label_put_price.config(text=f"Put Option Price: {put_price:.2f}")


root = tk.Tk()
root.title("Black-Scholes Option Pricing Model")


ttk.Label(root, text="Current Stock Price (S):").grid(row=0, column=0, padx=10, pady=5)
entry_S = ttk.Entry(root)
entry_S.grid(row=0, column=1, padx=10, pady=5)

ttk.Label(root, text="Strike Price (K):").grid(row=1, column=0, padx=10, pady=5)
entry_K = ttk.Entry(root)
entry_K.grid(row=1, column=1, padx=10, pady=5)

ttk.Label(root, text="Time to Maturity (T):").grid(row=2, column=0, padx=10, pady=5)
entry_T = ttk.Entry(root)
entry_T.grid(row=2, column=1, padx=10, pady=5)

ttk.Label(root, text="Risk-free Interest Rate (r):").grid(row=3, column=0, padx=10, pady=5)
entry_r = ttk.Entry(root)
entry_r.grid(row=3, column=1, padx=10, pady=5)

ttk.Label(root, text="Volatility (sigma):").grid(row=4, column=0, padx=10, pady=5)
entry_sigma = ttk.Entry(root)
entry_sigma.grid(row=4, column=1, padx=10, pady=5)


button_calculate = ttk.Button(root, text="Calculate Prices", command=calculate_prices)
button_calculate.grid(row=5, column=0, columnspan=2, pady=10)


label_call_price = ttk.Label(root, text="Call Option Price: ")
label_call_price.grid(row=6, column=0, columnspan=2, pady=5)

label_put_price = ttk.Label(root, text="Put Option Price: ")
label_put_price.grid(row=7, column=0, columnspan=2, pady=5)


root.mainloop()