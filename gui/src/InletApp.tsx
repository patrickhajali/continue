import styled from "styled-components";
import ComboBox from "./components/mainInput/ComboBox"; 
import { useDispatch, useSelector } from "react-redux";

import React, { createContext } from "react"; 

import {
    useEffect,
    useRef,
    useState,
    useContext,
    useLayoutEffect,
    useCallback,
    Fragment,
  } from "react";
import { GUIClientContext } from "./App";
import { setActive, setHistory } from "./redux/slices/sessionStateReducer";
import { RootStore } from "./redux/store";
import ContinueGUIClientProtocol from "./client/ContinueGUIClientProtocol";
import useContinueGUIProtocol from "./hooks/useContinueClient";
import useSetup from "./hooks/useSetup";

const InletDiv = styled.div`
overflow-y: scroll;
scrollbar-width: none;  
`;  


function InletApp() {


    const inletTextInputRef = useRef<HTMLInputElement>(null);
    const sessionState = useSelector((state: RootStore) => state.sessionState);

    const dispatch = useDispatch();
    const client = useContinueGUIProtocol(false);

    useSetup(client, dispatch)

    // const posthog = usePostHog();
    // const dispatch = useDispatch();

    const onInletTextInput = (event?: any) => {
        if (inletTextInputRef.current && client) {

          let input = (inletTextInputRef.current as any).inputValue;

          (inletTextInputRef.current as any).setInputValue("");
        console.log(input)
          sendInput(input);
        }

    };

    const sendInput = useCallback( 
        (input: string) => {
            const newHistory = [
                ...sessionState.history,
                {
                    name: "User Input",
                    description: '/edit ' + input, // PAH: hacky
                    observations: [],
                    logs: [],
                    step_type: "UserInputStep",
                    params: { user_input: input }, 
                    hide: false,
                    depth: 0,
                },
                ];
                const state = {
                history: newHistory,
                context_items: sessionState.context_items,
                };
            //   for (let contextItem of sessionState.context_items) {
            //     dispatch(
            //       addContextItemAtIndex({
            //         item: contextItem,
            //         index: newHistory.length - 1,
            //       })
            //     );
            //   }
                client.runFromState(state);
                newHistory.push({
                name: "Generating Response...",
                description: " ",
                observations: [],
                logs: [],
                step_type: "SimpleChatStep", // PAH: TODO
                params: {},
                hide: false,
                depth: 0,
                });
                dispatch(setHistory(newHistory));
                dispatch(setActive(true));
        
                
        },
        [client, sessionState.context_items]
        );
    
    return (
        <GUIClientContext.Provider value={client}>
            <InletDiv>
                <ComboBox 
                    isMainInput = {false}
                    onEnter={(e, _) => {
                        onInletTextInput(e);
                        e?.stopPropagation();
                        e?.preventDefault();
                    }}
                    ref = {inletTextInputRef}
                    />      
            </InletDiv>
        </GUIClientContext.Provider>

    );
};
  
export default InletApp;
  
